# Module 30 — Ads at the Big Platforms

> The ad-stack-by-platform tour. Each one combines the same ingredients (auction + CTR/CVR model + bidder + pacing + privacy stack) into distinctive products. An architect interviewing for an ads role needs the differences memorised.

---

## 1. Google Ads — Performance Max + Smart Bidding

### 1.1 Performance Max (PMax)

GA 2021. Replaced Smart Shopping (2022) and Local. Single campaign type across **Search, Display, YouTube, Discover, Gmail, Maps**. Advertiser provides:
- Asset groups (text, image, video, audio).
- Conversion goals.
- Audience signals (optional).

Google's AI handles audience selection, placement, creative selection, bidding. **~80% of Google's retail ad spend on PMax by 2024.**

Pain point: advertisers complain about lack of transparency. Aggregate placement reports came in 2023; channel-level breakouts in 2024.

### 1.2 Smart Bidding

- **tCPA** — target cost per acquisition.
- **tROAS** — target return on ad spend.
- **Maximise Conversions** — spend whole budget; max conversions.
- **Maximise Conversion Value** — spend whole budget; max revenue.
- **Enhanced CPC** (deprecated 2024) — bid adjustment of manual CPC.

Auction-time bidding: every auction independently scored. Module 27 covered.

### 1.3 Underneath: DCN-V2 + MMoE multi-task

Module 19 covered the YouTube ranking stack. Google Ads shares much of the infrastructure: TFRS / TF-Ranking, TFX pipelines, TPU training.

---

## 2. Meta Ads — Advantage+ and the iOS Recovery

### 2.1 Advantage+ Shopping Campaigns (ASC)

Launched Aug 2022. ML across FB + IG + Audience Network + Messenger. Advantage+ App Campaigns and Advantage+ Catalog Ads followed. **Advantage+ Audience** replaced manual targeting in 2024 — the advertiser provides goals; Meta picks the audience.

### 2.2 AEM — Aggregated Event Measurement

Meta's response to ATT. Constraints:
- 8 conversion events per domain max.
- Prioritization (advertisers choose which events matter most).
- Aggregated reporting; no per-user identifiers.

### 2.3 Conversions API (CAPI)

Server-side conversion sending. Bypasses browser-side restrictions (Safari ITP, ad blockers). Now standard.

### 2.4 Meta Lattice (2023)

Unified ranking model architecture replacing many vertical models. ~10× model size; consolidated training. The pre-HSTU production ranker family.

### 2.5 Andromeda (2024)

Next-gen retrieval using HSTU-derived generative retrieval, GPU feature processing on NVIDIA Grace Hopper. **~10kx candidate-pool expansion** vs prior systems.

---

## 3. Amazon Ads — Retail Media as Moat

### 3.1 Surfaces

- Sponsored Products (largest line item — ~60% of Amazon ad revenue).
- Sponsored Brands.
- Sponsored Display.
- Amazon DSP — programmatic incl. Twitch, IMDb TV / Freevee, Prime Video.
- Amazon Marketing Cloud (AMC) — clean room.

### 3.2 Why retail media is the moat

- **Purchase data is deterministic.** Amazon knows who bought what.
- **Conversion attribution is deterministic** for in-Amazon purchases.
- **Search intent is explicit** ("buy [product]").

These three combine to make Amazon's ad inventory among the most valuable per impression in the world.

### 3.3 Recent expansions

- **Prime Video Ads** (2024) — tens of billions of new impressions.
- **Amazon Retail Ad Service** (2024) — white-labels Amazon ad-tech to other retailers.

---

## 4. TikTok Ads — Symphony

### 4.1 Ad formats

- Spark Ads (boost organic posts).
- TopView, In-Feed, Branded Hashtag Challenge.
- Smart+ Performance Campaigns (2024) — PMax/Advantage+ equivalent.

### 4.2 Symphony AI Suite (May 2024)

- **Creative Studio** — text-to-video, AI avatars, dubbing.
- **Assistant** — copywriting / brief drafting.
- **Ads Manager AI** — recommendation engine for ad-ops decisions.

### 4.3 Search Ads (2024)

TikTok rolled out search-result ads after observing that ~58% of users use TikTok as a search engine.

---

## 5. Apple Search Ads (ASA)

App Store search results. Boomed post-ATT — Apple's first-party data wasn't affected.

- **ASA Basic** — CPI (cost-per-install), automated.
- **ASA Advanced** — CPT (cost-per-tap) keyword bidding.
- **Today / Search / Product-page ads** — three placement options.

Revenue trajectory: ~$300M (2019) → **~$5B+ (2024)** → tracking ~$10B by 2026 (Bernstein/Evercore estimates).

The ASA moat: Apple owns the App Store search, owns the device, and faces no cross-app tracking limitation for its own data.

---

## 6. Microsoft Ads

### 6.1 Bing + Audience Network + LinkedIn Ads

Microsoft Advertising spans:
- Bing Search Ads.
- Microsoft Audience Network.
- LinkedIn Ads (B2B; firmographic targeting).

### 6.2 Xandr (acquired 2021)

Was AppNexus / AT&T's ad tech. Now under Microsoft Advertising. Powers Netflix's ad tier ad-tech.

### 6.3 Copilot Ads — the LLM-era inventory

- **Copilot ads** — sponsored answers in Bing Copilot, M365 Copilot.
- "Ads for Chat" launched 2024.
- Pricing, brand safety, and attribution are still being defined for chat surfaces.

---

## 7. The Trade Desk (TTD)

Largest independent DSP. CTV-heavy.

### 7.1 Kokai (2024)

Their AI rebrand:
- Agentic media planning.
- Integrated identity (UID2).
- Predictive forecasting.

### 7.2 UID2 (Unified ID 2.0)

Open-source email-hashed identity. Operated by Prebid.org under TTD stewardship. The DSP-led alternative to Google's Privacy Sandbox direction.

---

## 8. Retail Media Networks (RMNs)

>$140B in 2024, projected ~$180B in 2026 (GroupM).

| RMN | Owner | Notes |
|---|---|---|
| **Amazon Ads** | Amazon | Original, biggest |
| **Walmart Connect** | Walmart | Walmart + **Vizio** (acquired 2024 for CTV) |
| **Roundel** | Target | |
| **84.51° / Kroger Precision Marketing** | Kroger | Loyalty-driven |
| **Sam's Club MAP** | Walmart/Sam's | |
| **Instacart Ads** | Instacart | CPG-favourite |
| **Uber Advertising** | Uber | In-app + Journey ads |
| **DoorDash Ads** | DoorDash | |
| **CVS Media Exchange** | CVS | Pharmacy first-party |
| **Best Buy Ads** | Best Buy | |
| **Home Depot Retail Media+** | Home Depot | |

Pattern: retailers monetise loyalty / transaction data via Criteo / CitrusAd / Pacvue / VeriSpot or in-house. Also the CTV on-ramp (Walmart-Vizio, Roku, Disney+, NBC Peacock).

---

## 9. Cross-platform comparison (architect cheat sheet)

| Dimension | Google Ads | Meta Ads | Amazon Ads | TikTok | ASA |
|---|---|---|---|---|---|
| Auction | GSP-like with quality | VCG (2018+) | Modified GSP | Modified second-price | Modified second-price |
| Auto-bidder | Performance Max | Advantage+ | Sponsored Products auto + DSP | Smart+ | ASA Basic/Advanced |
| Privacy posture | Privacy Sandbox | AEM, CAPI | First-party purchase data | Project Texas/Clover | First-party only |
| Generative creative | Asset Group + Gemini | Advantage+ Creative + Llama | Image generator (2024) | Symphony Creative Studio | Limited |
| Measurement | DDA + Lift Studies | Lift + AEM + CAPI | AMC | Lift Studies | First-party |
| Identity moat | Search + YouTube + Android | Logged-in social | Purchase data | Engagement signal | Device + App Store |

---

## 10. Sanity check

1. Performance Max consolidates many surfaces under one campaign type. What did advertisers gain and what did they lose vs the previous SKAG (single-keyword ad group) era?
2. Meta's Advantage+ Audience eliminates manual targeting in 2024. Why does the platform prefer to make these decisions instead of letting advertisers?
3. Apple Search Ads grew from $300M to $5B+ post-ATT. What's the structural advantage Apple had that other platforms didn't?
4. Walmart acquired Vizio in 2024. Connect this acquisition to the retail-media-network thesis.
5. Microsoft's "Copilot ads" are sponsored answers in chat. What three problems are still unsolved for this surface?
