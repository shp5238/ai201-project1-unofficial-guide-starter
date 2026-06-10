# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
University-specific career documents. 
It covers topics such as resume writing, cover letters, internships, career fairs, networking, LinkedIn profiles, interview preparation, and mentorship opportunities.

This knowledge is valuable because students often struggle to locate information scattered across multiple PDFs, webpages, guides, and FAQs maintained by the career center. Although the information exists on the official website, it is fragmented across many lengthy resources and can be difficult to navigate quickly. 
---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->


| # | Source | Type | Description | URL or location |
|---|--------|------|-------------|------------------|
| 1 |Career Development Plan |PDF |Build an action plan for this semester for your career journey. |USD sources |
| 2 |A.I. Tips and Resources for Career Development |PDF |Guide for using A.I. in your career development journey. |USD sources |
| 3 |A.I. Tips and Resources for Career Development: |PDF |Guide for using A.I. in your career development journey. |USD sources |
| 4 |RoadTrip Nation |URL |Watch stories from real people in a variety of fields to get advice and explore careers |https://roadtripnation.com/edu/sandiego |
| 5 |How to Prepare for a Job Interview |PDF |Definitive guide to preparing for a job interview |USD sources |
| 6 |Networking, LinkedIn, Professional Organizations, and Informational Interviews |PDF |A guide to building professional connections, leveraging LinkedIn, engaging with industry organizations, and conducting informational interviews to explore career paths and opportunities. |USD sources |
| 7 |CareerShift |URL |Search listings from multiple job boards, make company lists, and find key contact information. |https://www.careershift.com/?sc=Sandiego |
| 8 |Data Science Resume |PDF | DS resume|USD sources |
| 9 |Engineering Resume #1  |PDF |Engineering Resume Sample 1 |USD sources |
| 10 |Engineering Resume #2 |PDF | Engineering Resume Sample 2 |USD sources |
---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**
I will have a fixed chunk size at 200 tokens which is 150 words.  

**Overlap:**
100 tokens

**Reasoning:**
Some documents like resumes are dense and very structured, so the smaller chunks ensure that the AI extracts the relevant information accurately without confusing contexts. Even other documents are guides often arranged in bullet points, so it doesn't make sense to have extremely large chunks. 
---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 |What are some common skills in Data Science student resumes? |Technical Skills: SQL, Python, R, AWS, Tableau, Git, Statistics, Data Mining, Machine Learning |
| 2 |For a job interview, what are some tips for my thank you note? | Be timely, handwritten or email, be brief, and have flawless grammar. | 
| 3 |I want to network but don't know where to start. What are some USD-specific resources? | There are many options like T.E.A.M., Handshake, Torero Treks, and LinkedIn.  |
| 4 |Why should I use AI in my job preparation process? |AI can enhance career preparation by helping students practice interviews, receive personalized feedback, and identify skill gaps. It saves time by quickly synthesizing information such as job market trends and industry research, while also simulating perspectives like recruiters, hiring managers, and applicant tracking systems (ATS). Additionally, AI can improve resumes, cover letters, and other application materials by providing suggestions on clarity, structure, tone, and overall effectiveness. |
| 5 |How do I find salary and job outlook information? |Use resources such as O*NET Online and USD Student Outcomes data to research career outlooks, salary expectations, and employment trends for your field of interest. You can also watch informational interviews on Roadtrip Nation to gain insights from professionals and explore different career paths. |












---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. I think semantic search may retrieve chunks that contain similar words but discuss unrelated topics. This could cause the LLM to generate partially incorrect answers even when retrieval appears relevant.

2. Another challenge is that important information may span multiple adjacent chunks. If only one chunk is retrieved, the answer may be incomplete or missing critical context. I'll consider increasing chunk overlap to reduce this risk but cannot eliminate it entirely.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
