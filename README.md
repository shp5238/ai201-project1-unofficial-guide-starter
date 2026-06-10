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
| 1 |Career Development Planning Worksheet |PDF |Build an action plan for this semester for your career journey. |`USD sources/Career-Development-Planning-Worksheet.pdf` |
| 2 |A.I. Tips and Resources for Career Development |PDF |Guide for using A.I. in your career development journey. |`USD sources/Tips and resources for using AI for career development.pdf` |
| 3 |RoadTrip Nation |URL |Watch stories from real people in a variety of fields to get advice and explore careers. Surfaced as a recommended link, not chunked. |https://roadtripnation.com/edu/sandiego |
| 4 |How to Prepare for a Job Interview |PDF |Definitive guide to preparing for a job interview (behavioral questions, thank-you notes, offers). |`USD sources/tcg-interview-preparation.pdf` |
| 5 |Networking, LinkedIn, Professional Organizations, and Informational Interviews |PDF |A guide to building professional connections, leveraging LinkedIn, engaging with industry organizations, and conducting informational interviews to explore career paths and opportunities. |`USD sources/tcg-networking-informational-interviews.pdf` |
| 6 |CareerShift |URL |Search listings from multiple job boards, make company lists, and find key contact information. Surfaced as a recommended link, not chunked. |https://www.careershift.com/?sc=Sandiego |
| 7 |Data Science Resume |PDF |Sample Data Science résumé. |`USD sources/Copy of Data Science Resume.pdf` |
| 8 |Engineering Resume #1 |PDF |Engineering résumé sample 1. |`USD sources/Copy of Engineering Resume #1.pdf` |
| 9 |Engineering Resume #2 |PDF |Engineering résumé sample 2. |`USD sources/Copy of Engineering Resume #2.pdf` |

*Sources: 7 local PDFs (chunked) + 2 website tools (surfaced as recommended links, not chunked). The original source list double-counted the A.I. guide; this table lists the 9 distinct sources actually in the system.*


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
Each PDF is extracted with PyMuPDF (chosen over pdfplumber, which scrambled the glyph order on the `tcg-*` career-guide PDFs — e.g. "insgtr ongleyn" instead of "I strongly"). The raw extracted text is saved to `data/raw/` *before* any cleaning so the originals stay recoverable. Cleaning then: strips stray HTML tags, rejoins words split by a hyphen across a line break, collapses runs of spaces/tabs, trims trailing whitespace per line, and collapses 3+ blank lines into a single paragraph break. Cleaned text is saved to `data/cleaned/`. Token counts are measured with the all-MiniLM-L6-v2 tokenizer (the same one the embedder uses), so a "200-token chunk" means 200 tokens as the embedding model sees them.

*Known limitation:* `tcg-interview-preparation.pdf` includes a sample thank-you note rendered in a decorative handwriting font whose embedded Unicode map is broken (it maps `a`→`q`, etc.). Every PDF text extractor returns substituted letters for it ("Thqnk you /ortqkin'1..."); only OCR could recover it. The readable prose sections on thank-you notes extract correctly, so this affects only the decorative sample, not the guidance itself.

*Website sources:* RoadTrip Nation and CareerShift are interactive JavaScript apps with no useful prose to embed, so they are **not chunked**. They are registered in `data/resources.json` (name, URL, description, topic keywords) so the generation stage can recommend them when a user asks a related question.

**Final chunk count:**
130 chunks across the 7 local PDFs.


---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**
all-MiniLM-L6-v2 (sentence-transformers), loaded locally with `SentenceTransformer("all-MiniLM-L6-v2")` — no API key, no rate limits. Chunks are embedded with normalized 384-dim vectors and stored in a persistent ChromaDB collection (`career_chunks`) configured for **cosine** distance, with `source` and `chunk_index` metadata on each entry for later attribution. Queries are embedded with the same model; `retrieve(query, k=5)` returns the top-5 chunks with their text, source, and cosine distance. See [rag.py](rag.py).

**Production tradeoff reflection:**
If cost weren't a constraint, I'd consider a larger hosted embedding model (e.g. OpenAI or Voyage) for better accuracy on acronym-heavy, domain-specific resume text, plus a longer input window so each chunk could carry more context than MiniLM's 256-token limit. The tradeoffs: a hosted model adds per-call cost, network latency, and sends data off-machine, whereas MiniLM is free, private, and fast on CPU at the price of some accuracy and dimensionality. A multilingual model would only matter if the corpus included non-English documents, which this one does not.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
The `ask()` function in [rag.py](rag.py) sends the top-5 retrieved chunks to Groq `llama-3.3-70b-versatile` as a numbered context block, with a system prompt that constrains the model to that context. The key instructions are: *"Use ONLY information found in the provided context. Do not use outside or prior knowledge… If the context does not contain enough information to answer the question, reply with EXACTLY this sentence and nothing else: 'I don't have information on that in the USD career resources I have access to.'… Never fabricate sources, statistics, URLs, names, or quotes."* The model is also told **not** to cite sources itself. Generation runs at `temperature=0` for faithful (not creative) output. Tested: an out-of-scope question ("What time does the campus dining hall close on weekends?") returns the exact decline sentence rather than a hallucinated answer.

**How source attribution is surfaced in the response:**
Sources are attached **programmatically**, not by the model. After generation, `ask()` collects the `source` metadata of the retrieved chunks (de-duplicated, in order of first appearance) and returns them in a separate `sources` field — so attribution can't be hallucinated. If the model returns the decline sentence, no sources are attached (nothing was used). The web UI renders these inside the assistant's message bubble under a **Sources** label. Separately, the two website tools (RoadTrip Nation, CareerShift) are surfaced as recommended links from `data/resources.json` only when the question matches their topic keywords (e.g. a salary/job-outlook question surfaces RoadTrip Nation).

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What are some common skills in Data Science student resumes? | SQL, Python, R, AWS, Tableau, Git, Statistics, Data Mining, Machine Learning | Listed exactly those technical skills (plus a Six Sigma certification) drawn from the DS résumé | Relevant (top dist 0.45) | Accurate |
| 2 | For a job interview, what are some tips for my thank-you note? | Be timely, handwritten or email, brief, flawless grammar | Gave timely (within 24h), handwritten-or-email, brief, and flawless-grammar tips, plus what to include | Relevant (top dist 0.23) | Accurate |
| 3 | I want to network but don't know where to start. What are some USD-specific resources? | T.E.A.M., Handshake, Torero Treks, LinkedIn | Named the T.E.A.M. platform, Handshake, LinkedIn, Torero Treks, and career fairs | Partially relevant (top results were off-topic AI chunks; the correct networking chunk ranked #5) | Accurate |
| 4 | Why should I use AI in my job preparation process? | Practice interviews, personalized feedback, identify skill gaps, save time, simulate recruiters/ATS, improve materials | Covered all of: practice/feedback, time-saving, market research, simulating recruiters/ATS, skill-gap identification, and writing support | Relevant (top dist 0.32) | Accurate |
| 5 | How do I find salary and job outlook information? | O\*NET Online, USD Student Outcomes, RoadTrip Nation | Cited the Occupational Outlook Handbook + USD Student Outcome data, and surfaced RoadTrip Nation as a recommended link. **Did not mention O\*NET.** | Partially relevant (top dist 0.63) | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

**Summary:** 4 of 5 answers fully accurate; Q5 partially accurate (see Failure Case Analysis). Notably, Q3 produced a correct answer *despite* the top-ranked chunks being off-topic — retrieving k=5 meant the relevant networking chunk (ranked #5) was still in context for the LLM to use, which is exactly why top-k > 1 matters.

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
"How do I find salary and job outlook information?" (eval Q5). The expected answer includes **O\*NET Online**, USD Student Outcomes data, and RoadTrip Nation.

**What the system returned:**
"You can find salary and job outlook information by using online resources such as the Occupational Outlook Handbook, and USD's Student Outcome data… " — plus RoadTrip Nation surfaced as a recommended link. The answer was correct as far as it went, but **omitted O\*NET Online**, which was part of the expected answer.

**Root cause (tied to a specific pipeline stage):**
The **chunking stage**. In the Career Development Planning Worksheet, the resource list reads "…Search O\*NET Online and USD's Student Outcome data…", but the 200-token chunk boundary fell right inside that phrase: the retrieved chunk (#5) begins with the orphaned word *"Online and USD's Student Outcome data…"* — the "Search O\*NET" that precedes it landed in the previous chunk (#4), which did not rank in the top-5 for this query. So the embedding for chunk #5 never represented the token "O\*NET," and the LLM, grounded strictly in the retrieved context, could only report what survived the split. This is the chunk-boundary risk predicted in planning.md Anticipated Challenge #2. The high top distance (0.63) — Challenge #1, "salary/outlook" wording diluted by keyword overlap — compounded it by ranking the worksheet chunks lower.

**What you would change to fix it:**
Increase the chunk overlap (e.g. 100 → 125–150 tokens) so a key term like "O\*NET Online" can't be cleanly severed from its list, and/or add light structure-aware chunking that avoids cutting in the middle of a bullet/resource entry. A larger top-k (e.g. 8) would also pull in the neighboring chunk #4 that holds "Search O\*NET." Longer term, a higher-accuracy embedding model would rank the worksheet's salary/outlook content above the loosely-related chunks it currently competes with.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
Writing the Chunking Strategy and Architecture sections before any code meant the implementation had concrete targets instead of guesses. Because I'd already committed to 200-token chunks with 100-token overlap, all-MiniLM-L6-v2, ChromaDB with top-5, and Groq llama-3.3-70b, I could direct the AI to generate each stage against exact parameters rather than negotiating them mid-build. The Evaluation Plan questions doubled as my verification harness — I ran those five through retrieval and then end-to-end, which is how I caught that Q5 was only partially answered.

**One way your implementation diverged from the spec, and why:**
The spec listed two website URLs (RoadTrip Nation, CareerShift) as document sources to ingest, but I diverged by **not chunking them**. Once I inspected them they turned out to be interactive JavaScript apps with no substantive prose to embed, so chunking them would only have polluted retrieval with navigation boilerplate; instead I registered them in `data/resources.json` and surface them as recommended links when a question matches their topics. Two smaller divergences: the Architecture diagram just said "Python Loader," but pdfplumber scrambled the glyph order on two guide PDFs so I switched to PyMuPDF; and the spec planned a Gradio UI, but I built a custom Flask + HTML/CSS chat interface instead to get full control over the visual design (message bubbles, light/dark theme, help and clear-chat controls) that Gradio's component model couldn't produce.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1 — Ingestion and chunking (Milestone 3)**
* *What I gave the AI:* My Documents list and Chunking Strategy section (200-token chunks, 100-token overlap, with rationale), along with the Architecture diagram. I asked it to create a script that loads my PDFs, saves the raw text before cleaning, cleans the text, and then chunks it.
* *What it produced:* [ingest.py](ingest.py) containing a load_documents() function and a chunk_text() function. The script outputs chunks in the format {text, source, chunk_index} and stores them in data/chunks.json (130 chunks total).
* *What I changed or overrode:* (1) I had it count tokens using the actual all-MiniLM-L6-v2 tokenizer instead of estimating based on word count, so the 200-token chunk size matches what the embedding model actually receives. (2) After reviewing sample chunks, I noticed that text from two guide PDFs was not being extracted correctly, so I instructed it to switch from pdfplumber to PyMuPDF. (3) I decided not to follow the original plan of scraping the two URLs and instead treated them as a separate resource registry, since they did not need to be chunked.

**Instance 2 — Embedding, retrieval, and grounded generation (Milestones 4–5)**
* *What I gave the AI:* My Retrieval Approach section (all-MiniLM-L6-v2, ChromaDB, top-5 retrieval), the chunk schema from Milestone 3, the Architecture diagram, and the grounding requirement that responses must be based only on retrieved context, decline when context is insufficient, and return {answer, sources}.
* *What it produced:* [rag.py](rag.py) with embed_and_store(), retrieve(), and ask() functions, along with a [app.py](app.py) web UI.
* *What I changed or overrode:* (1) I had it configure ChromaDB to use cosine distance instead of the default squared-L2 distance, making the "distance < 0.5" threshold easier to interpret. (2) During evaluation, the correct chunk for Question 3 was ranked fifth, so I kept k=5 instead of reducing it because a smaller value would have excluded the chunk that actually contained the answer. (3) I chose to enforce grounding through the system prompt rather than a strict distance filter, since valid in-domain chunks had distances between 0.45 and 0.63 and could have been incorrectly filtered out. (4) I made source attribution come directly from chunk metadata so citations are generated from stored data rather than by the model itself.


**Video**
<div>
    <a href="https://www.loom.com/share/85e4ccb3863f42eb90332b8e31ea3e79">
      <p>University of San Diego — Career Assistant - 9 June 2026 - Watch Video</p>
    </a>
    <a href="https://www.loom.com/share/85e4ccb3863f42eb90332b8e31ea3e79">
      <img style="max-width:300px;" src="https://cdn.loom.com/sessions/thumbnails/85e4ccb3863f42eb90332b8e31ea3e79-d264734207417e25-full-play.gif#t=0.1">
    </a>
  </div>