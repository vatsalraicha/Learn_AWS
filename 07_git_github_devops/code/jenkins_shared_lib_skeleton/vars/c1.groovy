// vars/c1.groovy — Capital One shared library entry point
// Drop into a Git repo with structure:
//   vars/c1.groovy          (this file — global step `c1`)
//   vars/buildAndPushDocker.groovy
//   vars/deployToSageMaker.groovy
//   src/com/capitalone/pipeline/*.groovy
//   resources/*
//
// Configure as Global Pipeline Library in Jenkins:
//   Name: c1-pipeline
//   Source: GitHub
//   Branch: stable (or pin SHA in prod)
//
// Used from a Jenkinsfile:
//   @Library('c1-pipeline@v3') _
//
//   pipeline {
//     stages {
//       stage('Build') {
//         steps { c1.buildAndPushDocker(imageName: 'foo', tag: '1.2.3') }
//       }
//     }
//   }

import com.capitalone.pipeline.*

class C1Wrapper implements Serializable {
    def script

    C1Wrapper(script) { this.script = script }

    // ─── Build + push Docker image to ECR ──────────────────────────
    def buildAndPushDocker(Map args) {
        String imageName = args.imageName ?: script.error("imageName required")
        String tag = args.tag ?: script.env.GIT_COMMIT.take(8)
        String ecrAccount = args.ecrAccount ?: 'shared-cicd'

        script.container('docker') {
            script.withCredentials([
                script.string(credentialsId: "ecr-${ecrAccount}-account", variable: 'ECR_ACCOUNT_ID')
            ]) {
                script.sh """
                    aws ecr get-login-password --region us-east-1 | \
                        docker login --username AWS --password-stdin \
                        \${ECR_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

                    docker build \
                        -t \${ECR_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/${imageName}:${tag} \
                        -t \${ECR_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/${imageName}:latest \
                        .

                    docker push \${ECR_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/${imageName}:${tag}
                    docker push \${ECR_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/${imageName}:latest
                """
            }
        }
    }

    // ─── Model validation gate (fairness, performance, drift) ─────
    def modelValidationGate(Map args) {
        String configPath = args.configPath ?: 'configs/validation.yaml'
        List protectedAttrs = args.fairnessProtectedAttrs ?: ['age', 'gender']
        Double fairnessThreshold = args.fairnessThreshold ?: 0.80
        Double performanceThreshold = args.performanceThreshold ?: 0.85

        script.sh """
            uv run python scripts/validate_model.py \
                --config ${configPath} \
                --protected-attrs ${protectedAttrs.join(',')} \
                --fairness-threshold ${fairnessThreshold} \
                --performance-threshold ${performanceThreshold} \
                --output validation-report.json
        """
        script.archiveArtifacts 'validation-report.json'
    }

    // ─── Deploy to SageMaker endpoint via IRSA-assumed role ───────
    def deployToSageMaker(Map args) {
        String env = args.environment ?: script.error("environment required")
        String endpointName = args.endpointName ?: script.error("endpointName required")
        String modelPackageGroup = args.modelPackageGroup ?: script.error("modelPackageGroup required")
        String approvalStatus = args.approvalStatus ?: 'Approved'
        String strategy = args.deploymentStrategy ?: 'rolling'

        script.container('aws-cli') {
            // Agent's ServiceAccount → IRSA → IAM role in target account (via cross-account trust)
            script.sh """
                # Get latest approved model package
                MODEL_PACKAGE_ARN=\$(aws sagemaker list-model-packages \
                    --model-package-group-name ${modelPackageGroup} \
                    --model-approval-status ${approvalStatus} \
                    --sort-by CreationTime --sort-order Descending --max-results 1 \
                    --query 'ModelPackageSummaryList[0].ModelPackageArn' --output text)

                # Create model + endpoint-config
                MODEL_NAME=${endpointName}-\$(date +%s)
                CFG_NAME=${endpointName}-cfg-\$(date +%s)

                aws sagemaker create-model \
                    --model-name \$MODEL_NAME \
                    --containers ModelPackageName=\$MODEL_PACKAGE_ARN \
                    --execution-role-arn \$SAGEMAKER_EXECUTION_ROLE_ARN

                aws sagemaker create-endpoint-config \
                    --endpoint-config-name \$CFG_NAME \
                    --production-variants "[{
                        \\"VariantName\\":\\"variant-1\\",
                        \\"ModelName\\":\\"\$MODEL_NAME\\",
                        \\"InitialInstanceCount\\":2,
                        \\"InstanceType\\":\\"ml.m5.large\\"
                    }]"

                aws sagemaker update-endpoint \
                    --endpoint-name ${endpointName} \
                    --endpoint-config-name \$CFG_NAME

                aws sagemaker wait endpoint-in-service \
                    --endpoint-name ${endpointName}
            """
        }
    }

    // ─── Smoke test SageMaker endpoint ─────────────────────────────
    def smokeTestEndpoint(Map args) {
        String endpointName = args.endpointName ?: script.error("endpointName required")
        String payload = args.payload ?: '{"feature1": 1.0, "feature2": "test"}'

        script.container('aws-cli') {
            script.sh """
                aws sagemaker-runtime invoke-endpoint \
                    --endpoint-name ${endpointName} \
                    --content-type application/json \
                    --body '${payload}' \
                    response.json

                python -c "
                import json
                r = json.load(open('response.json'))
                assert 'prediction' in r or 'predictions' in r, 'No prediction in response'
                print('Smoke test passed')
                "
            """
        }
    }

    // ─── Notify Slack (factored centrally for consistent format) ──
    def notifySlack(Map args) {
        String channel = args.channel ?: '#deploys'
        String message = args.message ?: ''
        String color = args.color ?: 'good'

        script.withCredentials([
            script.string(credentialsId: 'slack-bot-token', variable: 'SLACK_TOKEN')
        ]) {
            script.sh """
                curl -X POST https://slack.com/api/chat.postMessage \
                    -H "Authorization: Bearer \$SLACK_TOKEN" \
                    -H "Content-Type: application/json" \
                    -d '{
                        "channel": "${channel}",
                        "attachments": [{
                            "color": "${color}",
                            "text": "${message}"
                        }]
                    }'
            """
        }
    }
}

def call() {
    return new C1Wrapper(this)
}

// Allow calling as `c1.foo(...)` via property accessor
def propertyMissing(String name) {
    def wrapper = new C1Wrapper(this)
    return wrapper."$name"
}

def methodMissing(String name, args) {
    def wrapper = new C1Wrapper(this)
    return wrapper.invokeMethod(name, args)
}
