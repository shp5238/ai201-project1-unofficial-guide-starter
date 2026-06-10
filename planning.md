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
all-MiniLM-L6-v2 via sentence-transformers. It runs locally with no API key and no rate limits, embeds fast on CPU, and its 384-dim vectors are a good fit for a small corpus (~130 chunks). Stored in ChromaDB using cosine distance.

**Top-k:**
5. Each chunk is only ~200 tokens, so a single chunk rarely holds a full answer; retrieving 5 gives the LLM enough surrounding context (and recovers content split across chunk boundaries — see Anticipated Challenge 2) without diluting the prompt with off-topic material.

**Production tradeoff reflection:**
If cost weren't a constraint, I'd weigh a larger embedding model (e.g. an OpenAI or Voyage embedding) for better accuracy on domain-specific/acronym-heavy resume text, and a longer context window so each chunk could carry more surrounding context. MiniLM's 256-token input limit and 384 dimensions trade some accuracy for speed and zero cost. For mostly-English career documents that tradeoff is reasonable, but a multilingual model would matter if the corpus included non-English résumés. The main latency/accuracy decision would be local CPU embedding (free, slower, private) vs. an API embedding (faster at scale, higher accuracy, but per-call cost and data leaving the machine).

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

> **Note from M3 (chunk inspection):** Confirmed in practice. Inspecting 5 representative chunks showed every chunk starts and/or ends mid-sentence (e.g. a resume chunk ended `"...May 2022 - Aug. 202"`, an AI-tips chunk ended `"###Job Description: [copy/paste"`), because the fixed 200-token window cuts across sentence and section boundaries. The 100-token overlap is what mitigates this — the clipped tail of one chunk reappears at the start of the next — so the information is recoverable as long as retrieval returns the neighboring chunk. Two smaller, lower-impact artifacts also showed up: embedded PDF page numbers (e.g. `56 57`) sprinkled into the text, and letter-spacing noise isolated to `tcg-networking-informational-interviews.pdf` (e.g. `"ce llphone"`, `"ski lled"`). Separately, a sample thank-you note in `tcg-interview-preparation.pdf` is rendered in a decorative handwriting font with a broken Unicode map (`a`→`q`), so it extracts as garbled text that no text extractor can recover — but the readable prose on thank-you notes extracts fine elsewhere.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---
## Architecture

```text
+----------------------+
| Document Ingestion   |
| TXT Files / PDFs     |
| Python Loader        |
+----------+-----------+
           |
           v
+----------------------+
| Chunking             |
| Custom Chunker       |
| Fixed Size + Overlap |
+----------+-----------+
           |
           v
+----------------------+
| Embedding +          |
| Vector Store         |
| all-MiniLM-L6-v2     |
| ChromaDB             |
+----------+-----------+
           |
           v
+----------------------+
| Retrieval            |
| Semantic Search      |
| Top-K = 5            |
+----------+-----------+
           |
           v
+----------------------+
| Generation           |
| Groq Llama-3.3-70B   |
| Grounded Responses   |
+----------------------+
```

**Tools Used**
* Document Ingestion: Python file loaders
* Chunking: Custom Python chunking function
* Embeddings: all-MiniLM-L6-v2 (Sentence Transformers)
* Vector Store: ChromaDB
* Retrieval: ChromaDB semantic similarity search (Top-5)
* Generation: Groq llama-3.3-70b-versatile



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
Tool: Claude
Input: My Documents section (local TXT/PDF files in a `/data` folder) + my Chunking Strategy section (chunk size, overlap, rationale) + the Architecture diagram above.
Expected output: A script with a `load_documents()` function that reads files from disk and cleans them (strips HTML tags, boilerplate, blank lines), and a `chunk_text()` function that splits cleaned text by my specified chunk size and overlap, returning a list of `{text, source}` dicts.
Verification: Print 5 random chunks and confirm each is readable, self-contained, and free of artifacts. Confirm total chunk count is between 50–2,000.

**Milestone 4 — Embedding and retrieval:**
Tool: Claude
Input: My Retrieval Approach section (all-MiniLM-L6-v2, ChromaDB, Top-K = 5) + the chunk schema from Milestone 3 (`{text, source}`) + the Architecture diagram.
Expected output: An `embed_and_store()` function that embeds chunks with `SentenceTransformer("all-MiniLM-L6-v2")` and upserts them into ChromaDB with `source` and `chunk_index` metadata; and a `retrieve()` function that takes a query string and returns the top-5 chunks with text, source, and distance score.
Verification: Run 3 evaluation questions through `retrieve()` and confirm returned chunks are on-topic and distance scores are below 0.5.

**Milestone 5 — Generation and interface:**
Tool: Claude
Input: My grounding requirement (answer only from retrieved context, decline if not covered) + desired output format (`{answer, sources}`) + the `retrieve()` function signature + the Gradio skeleton from the project instructions + the Architecture diagram.
Expected output: An `ask()` function that calls `retrieve()`, formats chunks into a context block, sends a grounding-enforcing system prompt to Groq `llama-3.3-70b-versatile`, and returns `{answer, sources}`; and an `app.py` Gradio UI with a question input, answer output, and sources output.
Verification: Confirm the system prompt explicitly restricts the LLM to retrieved context, sources are appended programmatically (not left to the model), and an out-of-scope question returns a decline instead of a hallucinated answer.