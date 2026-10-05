// Jenkinsfile — Capital One-style declarative pipeline for ML service
// Demonstrates: K8s agent, shared library, parallel CI, environment gates, IRSA-based AWS auth

@Library('c1-pipeline@v3') _

pipeline {
    agent {
        kubernetes {
            yaml '''
                apiVersion: v1
                kind: Pod
                spec:
                  serviceAccountName: jenkins-ml-agent       # IRSA-annotated ServiceAccount
                  containers:
                    - name: python
                      image: capitalone/python-ml-runner:3.11
                      command: ['sleep', '99d']
                      resources:
                        requests: { memory: "2Gi", cpu: "1" }
                        limits:   { memory: "8Gi", cpu: "4" }
                    - name: aws-cli
                      image: amazon/aws-cli:latest
                      command: ['sleep', '99d']
                    - name: docker
                      image: docker:24-cli
                      command: ['sleep', '99d']
            '''
            defaultContainer 'python'
        }
    }

    options {
        timeout(time: 60, unit: 'MINUTES')
        ansiColor('xterm')
        buildDiscarder(logRotator(numToKeepStr: '50'))
        timestamps()
    }

    environment {
        AWS_REGION    = 'us-east-1'
        PYTHON_VERSION = '3.11'
        IMAGE_NAME    = 'fraud-detector'
        IMAGE_TAG     = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(8)}"
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Setup') {
            steps {
                sh 'uv sync --extra dev --extra train'
            }
        }

        stage('CI — parallel') {
            parallel {
                stage('Lint') {
                    steps {
                        sh 'uv run ruff check src tests'
                        sh 'uv run ruff format --check src tests'
                    }
                }
                stage('Type check') {
                    steps { sh 'uv run mypy src --strict' }
                }
                stage('Security') {
                    steps {
                        sh 'uv run bandit -c pyproject.toml -r src'
                        sh 'gitleaks detect --source . --redact'
                    }
                }
                stage('Unit tests') {
                    steps {
                        sh '''
                            uv run pytest tests/unit -v \
                                --cov=src --cov-report=xml \
                                --junitxml=junit-unit.xml
                        '''
                    }
                    post {
                        always { junit 'junit-unit.xml' }
                    }
                }
            }
        }

        stage('Model validation') {
            when { anyOf { branch 'main'; changeRequest target: 'main' } }
            steps {
                script {
                    c1.modelValidationGate(
                        configPath: 'configs/validation.yaml',
                        fairnessProtectedAttrs: ['age', 'gender', 'race'],
                        fairnessThreshold: 0.80,
                        performanceThreshold: 0.85
                    )
                }
            }
        }

        stage('Build + push image') {
            when { branch 'main' }
            steps {
                container('docker') {
                    script {
                        c1.buildAndPushDocker(
                            imageName: env.IMAGE_NAME,
                            tag: env.IMAGE_TAG,
                            ecrAccount: 'shared-cicd'
                        )
                    }
                }
            }
        }

        stage('Trigger training pipeline') {
            when { branch 'main' }
            steps {
                container('aws-cli') {
                    sh '''
                        aws sagemaker start-pipeline-execution \
                            --pipeline-name fraud-detector-train \
                            --pipeline-parameters Name=ImageUri,Value=$ECR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG \
                            --query 'PipelineExecutionArn' --output text > pipeline-arn.txt
                    '''
                    archiveArtifacts 'pipeline-arn.txt'
                }
            }
        }

        stage('Deploy staging') {
            when { branch 'main' }
            steps {
                script {
                    c1.deployToSageMaker(
                        environment: 'staging',
                        endpointName: 'fraud-detector-staging',
                        modelPackageGroup: 'fraud-detector',
                        approvalStatus: 'Approved'
                    )
                }
            }
        }

        stage('Smoke test staging') {
            when { branch 'main' }
            steps {
                script {
                    c1.smokeTestEndpoint(endpointName: 'fraud-detector-staging')
                }
            }
        }

        stage('Deploy prod') {
            when { branch 'main' }
            input {
                message "Deploy fraud-detector to PROD?"
                ok "Yes — deploy"
                submitterParameter "DEPLOY_APPROVER"
                submitter "capitalone/ml-ops-leads"
            }
            steps {
                script {
                    echo "Deploy approved by: ${env.DEPLOY_APPROVER}"
                    c1.deployToSageMaker(
                        environment: 'prod',
                        endpointName: 'fraud-detector-prod',
                        modelPackageGroup: 'fraud-detector',
                        approvalStatus: 'Approved',
                        deploymentStrategy: 'shadow-then-canary'
                    )
                }
            }
        }
    }

    post {
        success {
            script {
                c1.notifySlack(
                    color: 'good',
                    channel: '#ml-deploys',
                    message: "Build #${env.BUILD_NUMBER} succeeded: ${env.JOB_NAME}"
                )
            }
        }
        failure {
            script {
                c1.notifySlack(
                    color: 'danger',
                    channel: '#ml-deploys',
                    message: "Build #${env.BUILD_NUMBER} FAILED: ${env.JOB_NAME} (${env.BUILD_URL})"
                )
            }
        }
        always {
            archiveArtifacts artifacts: 'junit-*.xml,coverage.xml', allowEmptyArchive: true
            cleanWs()
        }
    }
}
