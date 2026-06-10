# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

The University Career Assistant is a Retrieval-Augmented Generation (RAG) system that provides grounded answers using university career-center resources. The system covers topics such as resume writing, cover letters, internships, career fairs, networking, LinkedIn profiles, interview preparation, and mentorship opportunities.
This knowledge is valuable because students often struggle to locate information scattered across multiple PDFs, webpages, guides, and FAQs maintained by the career center. Although the information exists on the official website, it is fragmented across many lengthy resources and can be difficult to navigate quickly. The Assistant centralizes these resources and provides cited answers based on official university materials rather than generic career advice.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | Description | URL or File Path |
|---|--------|------|-------------|------------------|
| 1 |Career Development Plan |PDF |Build an action plan for this semester for your career journey. | |
| 2 |A.I. Tips and Resources for Career Development |PDF |Guide for using A.I. in your career development journey. | |
| 3 |A.I. Tips and Resources for Career Development: |PDF |Guide for using A.I. in your career development journey. | |
| 4 |RoadTrip Nation |URL |Watch stories from real people in a variety of fields to get advice and explore careers |https://roadtripnation.com/edu/sandiego |
| 5 |How to Prepare for a Job Interview |PDF |Definitive guide to preparing for a job interview | |
| 6 |Networking, LinkedIn, Professional Organizations, and Informational Interviews |PDF |A guide to building professional connections, leveraging LinkedIn, engaging with industry organizations, and conducting informational interviews to explore career paths and opportunities. | |
| 7 |CareerShift |URL |Search listings from multiple job boards, make company lists, and find key contact information. |https://www.careershift.com/?sc=Sandiego |
| 8 |Data Science Resume |PDF | DS resume| |
| 9 |Engineering Resume #1  |PDF |Engineering Resume Sample 1 | |
| 10 |Engineering Resume #2 |PDF | Engineering Resume Sample 2 | |


---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**
I will have a fixed chunk size at 200 tokens which is 150 words.  

**Overlap:**
100 tokens

**Why these choices fit your documents:**
Some documents like resumes are dense and very structured, so the smaller chunks ensure that the AI extracts the relevant information accurately without confusing contexts. Even other documents are guides often arranged in bullet points, so it doesn't make sense to have extremely large chunks. 

**Preprocessing before chunking**

**Final chunk count:**


---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

**Production tradeoff reflection:**

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
