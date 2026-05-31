# Research Methodology Guide
## What No AI Can Reliably Do — A 16-Week Skill-Building Progression

Your `agency-research` pipeline reliably answers **"what is happening"** (structural data: format mix, posting frequency, engagement benchmarks, hashtag presence). What fills the gap — **"why it is happening"** and **"what to do about it"** — is a human skill set that no scraper or LLM can replace.

This guide builds that skill set in seven levels over 16 weeks.

---

## Why This Guide Exists

The automated research pipeline was built to handle the structural layer:
- Content audit matrix — format/frequency counting
- Engagement benchmarking — relative ER comparison
- Hashtag landscape — sample-relative discovery

Five frameworks were removed from automation because they are unreliable without primary qualitative research:
- **SWOT** — needs brand persona depth (tone, response behavior, content mix), not just metrics
- **JTBD** — needs direct customer language (comments, DMs, reviews), not inferred patterns
- **CEP** — needs purchase moment data, not theme inference
- **Persona** — no demographic source exists in any scraper; age ranges are fabricated
- **SOV** — bot-inflated follower counts × scraper-approximated ER = fabricated math

The rule: **structural observation = automate. Strategic interpretation = human.**

---

## Level 1: Research Thinking
### Weeks 1–3

### 1.1 Hypothesis Formation Before Data Collection

Every research project starts with a question, not a dashboard. Opening your scraper before writing down what you expect to find means you will find confirmation of whatever you already believe.

**Before every research sprint, write three statements:**

1. What I think is true — *"Competitor X gets higher engagement because they post Reels 5x/week"*
2. What would prove me wrong — *"If their carousel posts outperform their Reels, my theory is wrong"*
3. What I would do differently if my hypothesis is wrong — *"I would shift budget from Reels to carousel design"*

**Exercise 1.1a — The Pre-Research Brief**

Before every research sprint, write a 1-page document:
- The business question the client needs answered (not "what are competitors doing" but "should we invest in video production this quarter")
- 3 hypotheses you hold right now
- What data would falsify each hypothesis
- What decision changes if the hypothesis is wrong

**Exercise 1.1b — The Assumption Audit**

Take your last 5 client strategy decks. For each strategic recommendation, answer:
- What evidence supported this?
- Was the evidence structural (scraper-grade) or interpretive (you inferred it)?
- If interpretive: what primary source could have confirmed or denied it?

**Level-up marker:** You can write a pre-research brief in under 10 minutes that a colleague could execute without clarifying questions. You catch assumptions before they become recommendations.

---

### 1.2 Asking the Right Questions

Bad research answers the wrong question precisely. "What hashtags do competitors use" gives you a list. "What discovery mechanism is actually driving follower growth for competitors" might reveal hashtags are irrelevant and it is all Explore page placement.

**Translate client goals into researchable questions that are:**
- Specific enough to be answerable
- Open enough to allow surprising answers
- Connected to a decision the client will actually make

**Exercise 1.2a — The Question Ladder**

Take a vague client request ("I want more engagement"). Build a ladder:

1. Surface: "How do we get more engagement?"
2. Diagnostic: "What type of engagement matters for this client's business model?"
3. Comparative: "Which competitors get meaningful engagement (not just likes) and what are they doing differently?"
4. Causal: "What is it about their approach that creates this outcome, and would it transfer to our client?"
5. Decision: "Given the above, what specific change should we test in the next 30 days?"

**Exercise 1.2b — The "So What" Filter**

Take any finding from your last automated report. Ask "so what?" three times:

- Finding: "Competitor posts 7x/week on Instagram"
- So what? "They have higher posting frequency than our client"
- So what? "Higher frequency might explain their higher reach"
- So what? "We should test increasing frequency... BUT only if frequency (not content quality) is the actual driver"

That final "but" is where real research begins.

**Level-up marker:** You instinctively distrust research questions that contain only "what" and push toward "why" and "under what conditions."

---

### 1.3 Distinguishing Correlation from Causation

Accounts posting at 7am get 20% more engagement in your data. This does not mean posting at 7am causes more engagement. It might mean accounts with highly engaged audiences tend to post at 7am because their audience is in a specific timezone.

**Exercise 1.3a — The Alternative Explanation Game**

For any "insight" from a research report, generate 3 alternative explanations:

- Observation: "Competitor's carousel posts get 3x more saves than their Reels"
- Explanation A: Carousels are inherently more saveable (format effect)
- Explanation B: Their carousels contain tactical how-to content while Reels are brand awareness (content type confound)
- Explanation C: Their audience demographics skew toward users who prefer static content (audience effect)

Then ask: which explanation, if true, would change your recommendation?

**Level-up marker:** You never present a single correlation as a causal finding. You always name at least one plausible alternative explanation.

---

## Level 2: Primary Research Skills
### Weeks 4–8

### 2.1 Customer Interviews for Social Strategy

JTBD, personas, and CEPs require actual customer voice. No scraper can tell you WHY someone followed an account, what purchase moment triggered their search, or what job they hired the brand to do. You need to talk to humans.

**The Switching Interview Framework (15–30 minutes, 5+ participants)**

Ask people who recently started following (or unfollowed) a brand in your client's category:

1. **Timeline:** "Walk me through the moment you decided to follow/unfollow. What was happening in your life?"
2. **Push/Pull:** "What was frustrating about what you were seeing before? What attracted you to this account?"
3. **Anxieties:** "Was there anything that almost made you NOT follow?"
4. **Habits:** "What were you doing instead before? What content were you consuming?"
5. **Outcome:** "Now that you follow them, what has changed? Do you actually see their content?"

**Never ask "why did you follow them?" — people post-rationalize.** Ask them to reconstruct the timeline.

**Exercise 2.1a — Comment Mining With JTBD Lens**

1. Pull 100 comments from a competitor's top-performing posts
2. Manually categorize each into a job type:
   - "I needed to know..." (information job)
   - "This made me feel..." (emotional job)
   - "I saved/shared this because..." (social job)
   - "This confirmed my decision to..." (validation job)
3. Identify the top 2–3 jobs being done
4. Interview 3 people who left those comment types to understand full context

**Exercise 2.1b — DM/Inquiry Mining**

If your client receives DMs, pull 20 recent ones. For each:
- What triggered this message?
- What was the person trying to accomplish?
- What content did they engage with before messaging?
- What language do they use to describe their problem?

This is where real Category Entry Points come from — not themes inferred from post captions.

**Level-up marker:** You can conduct a 20-minute interview that yields 3+ actionable insights without asking a leading question. You hear the difference between what people say they want and what their behavior reveals.

---

### 2.2 Survey Design for Social Audiences

Surveys give breadth where interviews give depth. Use surveys to validate patterns found in interviews, not to discover patterns.

**The 7-Question Validation Survey (under 3 minutes)**

1. Screening question — confirm they are in the target audience
2. Behavioral question — what they actually do, not what they think
3. Frequency question — how often, to gauge importance
4. Forced-rank question — prioritize between competing hypotheses
5. One open-end — capture language you did not anticipate
6. Demographic classifier — for segmentation
7. Willingness to follow up — for future interviews

**Rules:**
- Never ask "would you like X?" — people say yes to everything
- Always ask "when did you last do X?" — behavioral, verifiable
- Limit to 3 minutes completion time

**Exercise 2.2a — Instagram Stories as Micro-Research**

Use your client's Stories to run structured polls:
- A/B test content concepts before producing them
- Validate persona hypotheses ("Do you follow us because A or B?")
- Test category entry moments ("When do you think about [category]?")

Document findings in a running research log, not just Stories analytics.

**Level-up marker:** You can design a survey that yields data you cannot get from scraping. You know the difference between a leading and a neutral question.

---

### 2.3 Ethnographic Observation

People's stated behavior differs from their actual behavior. Watching how people use Instagram in real time reveals things no survey captures.

**Exercise 2.3a — The Scroll-Along**

Ask 3–5 people to let you watch them scroll their feed for 10 minutes. Do not ask questions during. Observe:
- What do they pause on? (not what they "engage" with — what catches attention)
- What do they scroll past quickly?
- Do they read captions or just look at images?
- What makes them tap into a carousel vs. skip?
- When do they switch between Stories, Reels, and Feed?

**Level-up marker:** You have observed 5+ people scrolling and can articulate 3 behaviors that contradict common social media advice.

---

## Level 3: Data Quality Judgment
### Weeks 6–10

### 3.1 When Scraped Data Is Enough vs. When You Need More

| Question | Scraped Data Sufficient? | Why |
|---|---|---|
| How often does competitor X post? | Yes | Directly observable |
| What formats does competitor X use? | Yes | Directly observable |
| What is competitor X's ER? | Mostly | Reliable for relative comparison only |
| Why is competitor X's ER higher? | No | Requires interpretation of confounds |
| Who is competitor X's audience? | No | Demographics not in public data |
| What job does their content do? | No | Requires customer voice |
| Should our client copy their approach? | No | Requires client's unique context |

**Exercise 3.1a — The Data Sufficiency Audit**

Take your last research report. For each recommendation, mark it:
- **GREEN** — based on directly observable structural data
- **YELLOW** — based on pattern inference (reasonable but unvalidated)
- **RED** — based on interpretation that requires primary research to confirm

If more than 30% of recommendations are RED, your research has a validity problem.

**Exercise 3.1b — The Bot Contamination Check**

Your research confirmed 9–20%+ of social media activity is automated. For your next client report:
1. Pull the top 50 commenters on a competitor's recent posts
2. Manually check 20 of them: real accounts? genuine activity?
3. What percentage appear to be bots or engagement pods?
4. Recalculate engagement rate excluding suspected bots
5. Does the conclusion change?

**Level-up marker:** You can assess whether any finding requires primary validation or can be trusted as-is. You have developed an intuition for "this number feels wrong."

---

### 3.2 Venue Bias

Data from one platform tells you about that platform's audience, not the brand's full audience. Instagram followers are not the same humans as LinkedIn followers — even if they overlap, their behavior differs by platform.

**Exercise 3.2a — The Cross-Platform Divergence Map**

For one client or competitor, compare:
- Top-performing content themes on Instagram vs. LinkedIn
- Engagement timing, comment depth, share behavior
- Topics that get traction on one platform but not the other

The divergence IS the insight. It tells you what each platform's audience actually values.

**Exercise 3.2b — The "Where Else" Question**

For any audience insight from Instagram data, ask: "Where else does this audience exist that I am not measuring?"
- Reddit threads about the category
- YouTube comments on related content
- Amazon/Google reviews for competing products
- Niche forums

Check one alternative source. Does it confirm or contradict your Instagram-derived insight?

**Level-up marker:** You never make audience claims based on single-platform data without explicitly noting the venue bias.

---

## Level 4: Triangulation
### Weeks 8–12

### 4.1 The Three-Source Rule

A finding from one source is a hypothesis. Two sources make it plausible. Three make it actionable.

**Three types of triangulation:**
1. **Source triangulation** — same question, different data sources (scraped metrics + customer interviews + industry reports)
2. **Method triangulation** — same question, different methods (quantitative analysis + qualitative observation + expert consultation)
3. **Time triangulation** — same finding, observed across multiple time periods (not just one snapshot)

**Exercise 4.1a — The Three-Source Validation**

Take your strongest current hypothesis about a client's strategy. Find three independent sources:

- Source 1 (Quantitative): What does scraped data say?
- Source 2 (Qualitative): What do actual humans in the audience say?
- Source 3 (Contextual): What do industry reports or analogous cases say?

If all three align: high confidence, recommend action.
If two align and one contradicts: investigate the contradiction — it often reveals nuance.
If all point different directions: you have a research question, not an insight.

**Exercise 4.1b — The Contradiction Hunt**

Deliberately look for findings that contradict each other:
- Scraper says high engagement, but interview subjects say they never see competitor X's content
- Industry report says video outperforms static, but your client's data shows the opposite
- Comment sentiment appears positive, but DMs reveal frustration

Contradictions are not problems — they are where the real insights live.

**Level-up marker:** You never present a finding without noting how many independent sources confirm it. You actively seek contradictions.

---

### 4.2 Weight of Evidence

Not all evidence is equally strong.

| Evidence Type | Strength for "What" | Strength for "Why" |
|---|---|---|
| Platform native analytics (first-party) | Very High | Very Low |
| Scraped competitor data | High (relative) | None |
| Customer interviews (5+) | Medium | Very High |
| Survey (100+ responses) | High | Low–Medium |
| Comment/DM analysis | Medium | Medium–High |
| Industry benchmarks | Medium | None |
| Expert opinion | Low | Medium |
| Gut feeling | Very Low | Varies |

**Exercise 4.2a — The Evidence Inventory**

For your next client strategy recommendation:
1. List every piece of evidence supporting it
2. Rate each on the hierarchy above
3. Identify gaps: strong on "what" but weak on "why"?
4. Plan one research activity to fill the weakest gap

**Level-up marker:** You can articulate why you believe something and honestly assess the strength of your evidence. You comfortably say "I don't know yet — here is how I would find out."

---

## Level 5: Pattern Recognition vs. Noise
### Weeks 10–14

### 5.1 Signal Detection

Most variation in social media metrics is noise. A post that gets 2x the average engagement might be random variance, not a signal about what works.

**Exercise 5.1a — The Baseline Variance Test**

For any client or competitor, pull 90 days of posting data:
1. Calculate mean and standard deviation of engagement rate
2. A post is a genuine outlier only if it exceeds mean + 2 standard deviations
3. How many "top performing" posts from your last report are actually within normal variance?
4. Only true outliers deserve investigation into "why"

**Exercise 5.1b — The Confirmation Bias Trap**

Take a trend you believe is real ("our client's audience prefers carousel posts"). Now:
1. Write down what data confirmed this belief
2. Actively search for data that contradicts it (carousels that underperformed)
3. Calculate the ratio: how many outperform vs. underperform average?
4. If less than 60/40, your "pattern" might be noise

**Exercise 5.1c — Regression to Mean**

When a client says "our last post was amazing, let's do more of that":
1. Was the post a genuine outlier (above 2 SD)?
2. If yes: the next post in the same format will almost certainly perform worse — not because the format is bad, but because extreme performance naturally regresses to average
3. Only recommend "do more of this" after 5+ posts in the same format consistently outperform

**Level-up marker:** You can explain to a client why a single viral post does not constitute a strategy.

---

### 5.2 Observations vs. Insights

**Observation:** "Competitor X posts 3 carousels per week and gets high engagement."

**Insight:** "Competitor X's audience uses their carousels as reference material (high saves) — meaning the audience is in active learning mode, not passive scrolling. This creates an opportunity for our client to serve that same need with their unique expertise."

The difference:
- Observations describe what is happening (your scraper can do this)
- Insights explain WHY it matters and WHAT TO DO about it (only you can do this)

**The full insight chain:**
> Observation + **because** [why is this happening] + **which means** [what does this imply] + **therefore** [what specific action follows]

If you cannot add all three, it belongs in the appendix, not the recommendation.

**Exercise 5.2a — The Insight Upgrade**

Take 5 observations from your last research report. For each, add the full chain. If you cannot, note what primary research would be needed to complete it.

**Level-up marker:** Every finding you present contains the full chain. You can immediately tell the difference between an observation and an insight.

---

## Level 6: The Feedback Loop
### Weeks 12–16

### 6.1 Research-to-Test Pipeline

Research that does not change behavior is expensive curiosity. Every finding should connect to a specific, measurable change.

**The Test Card**

For every research insight, create:

```
INSIGHT:    [What you found]
HYPOTHESIS: [If we do X, then Y will happen, because Z]
TEST:       [Specific action to take]
METRIC:     [How we will measure success]
TIMELINE:   [How long to run the test]
DECISION:   [If metric exceeds/falls below threshold, we will...]
```

Example:
```
INSIGHT:    Competitor's audience saves carousels as reference material
HYPOTHESIS: If we create "save-worthy" reference carousels (checklists, frameworks,
            step-by-steps), save rate will increase 50%+ within 4 weeks
TEST:       Publish 2 reference carousels per week for 4 weeks
METRIC:     Save rate per post, reach growth from Explore
TIMELINE:   4 weeks
DECISION:   If save rate +50%: shift 30% of content budget to carousel production
            If not: investigate whether content quality or topic selection was wrong
```

**Exercise 6.1a — The Monthly Research Retrospective**

Every month, review:
1. What research findings did we act on?
2. What was the result?
3. Was the result what we predicted?
4. If not: was our research wrong, execution wrong, or did conditions change?
5. What do we now believe differently than 30 days ago?

**Level-up marker:** You can show a client the chain from "research finding" → "strategy change" → "measured outcome" for at least 3 past recommendations.

---

### 6.2 The Belief Inventory

**Per-client living document:**

| What We Believe | Evidence Strength | Last Validated | Status |
|---|---|---|---|
| Carousel posts drive saves for this audience | Strong (3 sources) | 2026-03 | Active |
| 7am posting drives reach | Working (1 test) | 2026-04 | Needs retest |
| Competitor X's growth is organic | Hunch | Never | Test pending |

**Strength levels:**
- **Strong** — confirmed by 3+ independent sources, tested, validated. Requires substantial contradictory evidence to revise.
- **Working** — supported by 1–2 sources, not yet tested. Should be revised if test results contradict.
- **Hunch** — based on experience/intuition, no formal evidence. Test before acting.

Anything not revalidated in 90 days drops one tier. Anything contradicted by test results gets explicitly retired.

**Level-up marker:** You can tell a client "we used to believe X, but testing showed Y, so we updated our approach to Z." You are comfortable being wrong publicly.

---

## Level 7: The Human Judgment Layer
### Ongoing

### 7.1 Contextual Reading

Interpret data within the specific context of the brand. No AI has sat in the client meetings, heard the founder's story, watched the audience evolve over 6 months, or felt the shift when a competitor launched something new.

**The Context Stack — activate before interpreting any data:**

1. What phase is this brand in? (Launch / Growth / Mature / Pivoting)
2. What happened last month that might affect current data?
3. What is the competitive environment doing right now?
4. What is the client's emotional state? (Excited? Anxious? Impatient?)
5. What does the client need to hear vs. what do they want to hear?

A 5% engagement rate means something different for a brand with 1K followers vs. 100K, for a brand in launch mode vs. maintenance mode.

---

### 7.2 Brand Intuition

Accumulated pattern-matching from working with many brands. When something is "off" before data confirms it. Not mysticism — compressed experience.

**How to build it deliberately:**

- **Post-mortem every surprise.** When something unexpected happens, write down what you expected vs. what happened vs. what you should have noticed earlier.
- **Cross-pollinate.** The pattern you see in a fitness brand might apply to a fintech brand. Keep a "patterns that transfer" notebook.
- **Trust discomfort.** When data says one thing but something feels wrong, investigate. Your intuition is detecting a pattern your conscious analysis hasn't articulated yet.

**Exercise 7.2a — The Weekly Discomfort Log**

Every Friday, write down:
- 1 thing in client data that "felt wrong" even if numbers looked fine
- 1 thing that worked better than expected
- 1 thing a competitor did that surprised you

After 12 weeks, review. You will find patterns in your discomfort that reveal developing intuition.

---

### 7.3 The Decision Journal

For every major strategic recommendation (not tactical, but directional), record:

1. What you recommended
2. What alternatives you considered
3. What made you choose this over alternatives
4. What evidence supported it
5. Your confidence level (1–10)
6. *(Fill in later)* What actually happened

Review quarterly to calibrate — to get better at knowing when your confidence should be high vs. low.

---

## Integration With Your Pipeline

```
AUTOMATED (agency-research)      →  HUMAN LAYER (this guide)
──────────────────────────────────────────────────────────────
Content audit matrix              →  "Why do these formats work?" (interviews)
Engagement benchmarking           →  "Is this real or bot-inflated?" (Level 3)
Hashtag landscape                 →  "Do people actually discover via these?" (observation)
Posting frequency data            →  "Is frequency the driver or a confound?" (triangulation)
Competitor format mix             →  "What job does this content do?" (JTBD interviews)
```

The automated layer tells you WHAT to investigate. The human layer tells you whether it is real and what to do about it.

---

## 16-Week Implementation Calendar

| Week | Focus | Key Activity | Output |
|---|---|---|---|
| 1 | Pre-research briefs | Write briefs for 3 current clients | 3 hypothesis documents |
| 2 | Question design | Rebuild research questions for 1 client | Question ladder document |
| 3 | Assumption audit | Audit last 5 strategy decks | Color-coded audit |
| 4 | Interview prep | Design interview guide, recruit 5 participants | Interview script |
| 5 | First interviews | Conduct 5 switching interviews | Transcripts + notes |
| 6 | Comment mining | Manual JTBD coding of 100 comments | Categorized language map |
| 7 | Survey design | Build validation survey from interview findings | 7-question survey |
| 8 | Data quality audit | Bot check + venue bias analysis for 1 client | Quality assessment |
| 9 | Triangulation | Three-source validation on strongest hypothesis | Evidence inventory |
| 10 | Contradiction hunting | Find 3 contradictions in current client data | Contradiction register |
| 11 | Statistical basics | Baseline variance calculation for 3 clients | Outlier thresholds |
| 12 | Insight upgrade | Convert 10 observations into full insight chains | Upgraded report |
| 13 | Test card creation | Build test cards for top 3 recommendations | Test backlog |
| 14 | First feedback loop | Run 1 test, measure, document | Test result card |
| 15 | Belief inventory | Create living belief document for 2 clients | Belief inventory |
| 16 | System integration | Build this into recurring workflow | Process document |

---

## Recommended Reading

| Book | Why It Matters |
|---|---|
| "The Mom Test" — Rob Fitzpatrick | Customer interview skills. Short, practical, directly applicable. |
| "Thinking in Bets" — Annie Duke | Decision-making under uncertainty. Calibrating confidence levels. |
| "How to Lie with Statistics" — Darrell Huff | Data judgment. Classic 1-hour read. |
| "Seeing What Others Don't" — Gary Klein | How insights actually form from pattern recognition. |
| "Calling Bullshit" — Bergstrom & West | Modern data literacy for AI-generated and social media claims. |

---

## The Ultimate Level-Up Markers

You have mastered this when you can:

1. Look at an automated research report and immediately identify which findings are trustworthy vs. which require validation
2. Conduct 5 customer interviews and extract strategic insights no scraper could reveal
3. Present a strategy recommendation with a clear evidence chain showing multiple independent sources
4. Show a client how a research finding led to a strategy change that produced measurable results
5. Comfortably say "I don't know yet — here is how I would find out" instead of fabricating an interpretive answer
6. Distinguish between noise and signal in any dataset from experience and judgment alone
7. Update your beliefs publicly when evidence contradicts them, and show clients why that is a strength
