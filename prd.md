# RescueDesk AI — Product Requirements Document (PRD)

**Document version:** 1.0  
**Status:** Hackathon MVP plan  
**Competition:** AppBuildersPH Hackathon 2026  
**Submission deadline stated in the supplied slides:** October 10, 2026, 10:00 AM  
**Product type:** Local-first, offline-capable emergency preparedness assistant  
**Working name:** RescueDesk AI

---

## 1. Executive Summary

RescueDesk AI is a desktop-first application that helps people prepare for emergencies and find answers in trusted emergency-preparedness documents—even when internet access is unavailable.

The product combines two capabilities:

1. **Local Emergency Assistant:** preparedness checklists and access to emergency reference material.
2. **Local Document Assistant:** document import, local text extraction, question answering grounded in document passages, and source references.

The product's defining feature is not simply that it serves Filipino users or provides emergency information. Its defining feature is that meaningful AI inference runs on the user's device, allowing the core workflow to continue without a cloud AI service.

### Product promise

> Ask questions about your emergency guides and prepare with confidence—even when the internet is unavailable.

### MVP principle

Build a small, reliable, demonstrable product. Prioritize offline operation, grounded answers, source references, and a polished demonstration over a broad feature list.

---

## 2. Competition Requirements and Product Strategy

The supplied AppBuildersPH Hackathon slides specify that the product must use AI running locally on a user's device to solve a real problem. The slides also state that cloud APIs may be used as secondary components, but core Local AI functionality must not depend entirely on a cloud AI API.

The slides list these judging weights:

| Criterion | Weight | RescueDesk AI strategy |
|---|---:|---|
| Problem & Usefulness | 25% | Address emergency preparedness and access to guidance during connectivity outages. |
| Local AI Implementation | 25% | Run the language model locally and answer from locally stored reference material. |
| Technical Execution | 20% | Demonstrate the full workflow reliably with the network disconnected. |
| Innovation | 15% | Combine emergency preparedness with private, source-grounded local document AI. |
| Product & Demo Quality | 15% | Provide a clear, accessible interface and a convincing offline demonstration. |

The competition slides also require the submission to disclose models, technologies/frameworks, APIs/cloud services, existing code/assets, and AI development tools. The slides require a demo video, an X or LinkedIn video URL, and a description of what runs locally versus what requires internet.

**Important:** These criteria are competition requirements transcribed from the supplied slides. The implementation choices and product strategy in the rest of this PRD are recommendations, not official competition rules.

---

## 3. Problem Statement

During a severe weather event or other emergency, a person may need to consult preparedness guides while internet connectivity is slow, unreliable, or unavailable. Important information may be buried in long PDF documents, and generic AI services may be unavailable offline or require sending content to a remote service.

RescueDesk AI addresses this by keeping reference documents and AI inference on the user's computer, making relevant guidance easier to find without requiring cloud inference for the core experience.

### Target users

**Primary**
- Individuals and families preparing for typhoons, floods, earthquakes, and other emergencies.
- People who want to keep emergency guides available offline.

**Secondary**
- Students and community volunteers who need to consult preparedness materials.
- Small organizations that want a local reference assistant for approved preparedness documents.

### Jobs to be done

- “Help me find the relevant instructions in my emergency guide.”
- “Help me prepare a household emergency checklist.”
- “Let me consult information even when my internet connection is down.”
- “Show me the source behind an AI-generated answer.”
- “Keep my imported documents and chat history on my device.”

---

## 4. Product Goals

### MVP goals

1. Demonstrate meaningful AI inference on the user's device.
2. Answer questions using locally available reference documents.
3. Show the source document and page or section supporting an answer, where available.
4. Support the core question-answering workflow with the internet disconnected after setup.
5. Provide a basic emergency-preparedness checklist.
6. Keep imported document content, checklist state, and chat history local by default.
7. Deliver a stable, polished demo suitable for the hackathon.

### Non-goals for the MVP

- Replacing emergency services, medical professionals, or official public advisories.
- Providing live disaster alerts, live weather, or real-time evacuation routing.
- Automatically detecting the user's location.
- Building a social/community reporting platform.
- Supporting multiple user accounts or cloud synchronization.
- Building native iOS and Android applications.
- Training a custom AI model.
- Guaranteeing that generated answers are always correct.

---

## 5. MVP Scope and Requirements

### P0 — Must have

#### FR-01: Offline-ready home dashboard
- Display the app name and a clear Local AI status.
- Show whether the local model is available.
- Show the document library and preparedness checklist entry points.
- Distinguish “model ready” from “offline test passed”; do not imply offline operation has been verified merely because a model is installed.

**Acceptance criteria**
- The user can identify whether the local model is ready.
- The dashboard does not require a remote AI service to load after initial setup.

#### FR-02: Local document library
- Include a small set of approved emergency-preparedness reference documents with the demo.
- Allow importing PDF and plain-text files if time and PDF extraction quality permit.
- Keep imported files and extracted text on the local device.
- Display document name and basic processing status.
- Allow users to remove imported documents and their locally indexed content.

**Acceptance criteria**
- At least one bundled reference document can be searched and used in the demo.
- A user can see which documents are available.
- Removing a document removes its extracted content from the app's local index.

#### FR-03: Local text extraction and indexing
- Extract text from supported PDFs and text files on-device.
- Split extracted text into manageable passages.
- Retain document name and page or section metadata where available.
- Make passages searchable locally.

**Acceptance criteria**
- A question can retrieve relevant passages from the bundled reference document without a network request.
- Unsupported or scanned PDFs produce a clear message rather than a silent failure.

#### FR-04: Local AI question answering
- Send the user's question and retrieved passages to a model running locally.
- Instruct the model to answer only from the supplied context.
- If the context is insufficient, respond that the available documents do not contain enough information.
- Do not call a cloud AI API for the core answer generation.

**Acceptance criteria**
- The app answers a predefined set of questions about the bundled reference guide.
- The app can be demonstrated answering a question with the network disconnected after setup.
- If relevant passages are not found, the app avoids inventing a definitive answer.

#### FR-05: Source references
- Display the source document and page or section when that metadata exists.
- Make the relevant supporting passage visible to the user.
- Clearly distinguish source text from the AI's summary or explanation.

**Acceptance criteria**
- At least one demo answer includes a source reference that can be checked against the original document.
- References are based on retrieved text, not invented by the model.

#### FR-06: Emergency preparedness checklist
- Provide a concise, editable checklist for preparedness tasks and essential supplies.
- Let the user mark items complete and undo the action.
- Save checklist state locally.
- Use vetted, general preparedness content and avoid implying that one checklist fits every emergency or household.

**Acceptance criteria**
- The user can check and uncheck items.
- State persists after restarting the app.
- The checklist works without internet access.

#### FR-07: Local storage and privacy
- Store document metadata, extracted passages, checklist state, and chat history locally.
- Do not transmit document contents or questions to a remote AI provider.
- Provide a way to clear chat history and remove documents.
- Avoid collecting unnecessary personal information.

**Acceptance criteria**
- The team can explain where app data is stored.
- Core interactions generate no external AI API calls.
- A clear-history action removes saved chat history.

#### FR-08: Error and safety handling
- Show understandable messages if the local model is unavailable, a document cannot be read, or no relevant passages are found.
- Display a persistent notice that RescueDesk AI is a preparedness reference tool, not an emergency dispatch or live alert service.
- Encourage users to follow current instructions from relevant official authorities and contact local emergency services when necessary.
- For medical or other safety-critical questions not supported by approved documents, avoid improvising instructions.

**Acceptance criteria**
- Model-unavailable and unsupported-document states are tested.
- The app does not represent generated content as an official emergency order.
- The app can clearly say when it does not know.

### P1 — Should have if time permits

- Search documents by title.
- Show processing progress for imported documents.
- Keep a small local conversation history with a delete option.
- Provide a one-click sample question to make the demo easy to follow.
- Add a “Test offline workflow” checklist for the presenter.
- Improve keyboard navigation, readable typography, and contrast.

### P2 — Future scope, not for the hackathon MVP

- Optical character recognition for scanned PDFs.
- Local embeddings and vector search.
- Local speech input or text-to-speech.
- Multiple language support, including Filipino and Taglish.
- Household profiles and personalized emergency plans.
- Optional, explicitly enabled synchronization.
- Live official alerts and weather integrations.
- Native mobile apps.
- Community resource mapping.

Do not start P1 or P2 features until every P0 acceptance criterion has been tested.

---

## 6. User Experience and Main Screens

### Screen 1: Home dashboard
- Product name and short purpose statement.
- Local model readiness indicator.
- Offline status / last test result, accurately labelled.
- Buttons or navigation for “Ask the Guide,” “Documents,” and “Preparedness Checklist.”
- Short safety disclaimer.

### Screen 2: Ask the Guide
- Chat question field.
- Suggested sample questions.
- AI answer area.
- Source document and page/section reference.
- Expandable supporting passage.
- “Not enough information in the available documents” state.
- Clear conversation action.

### Screen 3: Documents
- List of bundled and imported documents.
- Import control for supported file types.
- Document processing status.
- Remove-document action.
- Clear explanation that documents are processed locally.

### Screen 4: Preparedness Checklist
- Group items into practical categories such as supplies, communication, and household preparation.
- Checkboxes and completion state.
- Local persistence.
- Content reviewed against suitable public preparedness guidance before the demo.

### Screen 5: Privacy and About
- Explain that the model runs locally.
- Explain what data is stored locally.
- Disclose that internet is required for initial installation/model download.
- State known limitations and how to delete local data.
- Show the model name and version where available.

### UX principles
- Calm, clear, and accessible; avoid alarmist visuals.
- Prioritize readability and large, obvious controls.
- Keep the main action obvious: ask a question or open a checklist.
- Do not use a “safe” or “verified” badge unless the claim is actually supported.
- Make offline capability testable rather than relying on a decorative badge.

---

## 7. Recommended Technical Architecture

### Recommended MVP stack

| Layer | Recommendation | Reason |
|---|---|---|
| UI | HTML, CSS, JavaScript | Fast to implement and polish. |
| Local backend | Python + Flask | Simple local HTTP server and integration layer. |
| Local model runtime | Ollama, subject to hardware compatibility | Convenient local model management and inference. |
| Model | A small instruction-tuned model supported by the computer | Balance response quality, memory use, and latency. Select only after checking hardware. |
| PDF extraction | PyMuPDF | Extract text and page metadata from text-based PDFs. |
| Search | Local keyword search initially | Simpler and easier to validate under time pressure. |
| Storage | SQLite | Local persistence for metadata, checklist state, and chat history. |
| Version control | Git and a public GitHub repository | Required for the submission according to the supplied slides. |

These are recommendations, not mandated competition technologies. The final model choice depends on the operating system, RAM, available disk space, and GPU or Apple Silicon hardware.

### Request flow

1. User imports a document.
2. Backend extracts text locally.
3. Text is split into passages and indexed locally with source metadata.
4. User asks a question.
5. Local search retrieves the most relevant passages.
6. Backend sends the question and passages to the local model runtime.
7. Model generates an answer constrained to the retrieved context.
8. UI displays the answer and corresponding source references.
9. Optional chat and checklist state is saved locally.

### Local versus internet-dependent behavior

**Runs locally after setup**
- App interface and local backend.
- Document extraction and indexing.
- Document search.
- Local model inference.
- Checklist and chat-history storage.
- Source display.

**May require internet before the demo**
- Installing dependencies.
- Downloading the local model.
- Cloning the repository.
- Retrieving reference documents, if they are not bundled.

**Not required in the MVP**
- Cloud AI APIs.
- Cloud database.
- Analytics or remote document processing.
- Live weather or alert APIs.

### Important implementation note

The app should bind its local server to the loopback interface by default, avoid exposing uploaded documents to the local network, and validate uploaded file types and sizes. Do not claim that a product is secure merely because it runs locally; local access controls and safe file handling still matter.

---

## 8. Local AI and Retrieval Strategy

### MVP approach: retrieval-augmented generation (RAG), kept local

Use a simple local retrieval pipeline:
- Extract document text.
- Split it into passages while preserving page metadata.
- Search for relevant passages using keyword matching.
- Pass only the relevant passages to the local model.
- Ask the model to answer based on those passages and indicate when the answer is unsupported.

This avoids the additional setup and debugging involved in a vector database during the initial build.

### Model selection requirements
Choose the model only after confirming the development/demo computer's hardware.

Evaluate:
- Whether the model runs locally with no external inference.
- Memory and disk requirements.
- Time to load and answer a question.
- Answer quality on the selected reference guide.
- Ability to follow instructions to avoid unsupported answers.

### Evaluation questions
Prepare at least five questions before the demo:
1. A straightforward question whose answer is explicitly in the guide.
2. A question requiring combining two relevant passages.
3. A question whose answer is not in the document.
4. A question phrased differently from the source wording.
5. A safety-sensitive question that should be refused or redirected when unsupported.

For each, manually verify the answer and source reference against the original document.

---

## 9. Data and Content Requirements

- Bundle a small number of trusted, relevant emergency-preparedness references.
- Record each source's title, issuing organization, source URL, access date, and usage/license information.
- Prefer official or authoritative public guidance.
- Verify that the source content is suitable for offline redistribution and include attribution where required.
- Do not create fake official documents or represent demo material as a current government order.
- Add a clear note that downloaded guidance can become outdated.
- Use synthetic or non-sensitive demo documents; do not use private user records in the public demo.

Because this is an emergency-related product, content selection and validation are core product work, not just sample-data preparation.

---

## 10. Non-Functional Requirements

### Offline reliability
- Core question answering and checklist functions must work without internet after setup.
- No hidden dependency on a cloud AI API.
- The UI must handle model startup delays and unavailable-model states.

### Performance
- The app should remain responsive while processing a small demo document.
- Show loading/progress feedback for extraction and inference.
- Set a reasonable document-size limit for the MVP and explain it to users.
- Record actual response times during testing instead of promising a fixed speed before hardware is known.

### Privacy
- Keep document text and conversation data on-device by default.
- Do not include telemetry in the MVP unless explicitly disclosed and genuinely needed.
- Provide deletion controls for stored documents and chat history.

### Usability and accessibility
- Readable text, strong contrast, keyboard-accessible controls, and understandable error messages.
- The main demo flow should not require technical knowledge.
- Explain the local model and offline setup in plain language.

### Reliability and safety
- Do not present unsupported model output as authoritative guidance.
- Show sources where available.
- Do not substitute for live official warnings, emergency responders, or medical advice.
- Test common failure modes before recording the demo.

---

## 11. Test Plan and Definition of Done

The MVP is ready for submission only when the following critical checks pass.

### Functional tests
- [ ] App opens after installation and model setup.
- [ ] Bundled reference document appears in the library.
- [ ] Supported PDF or text file can be imported.
- [ ] Extracted text can be searched locally.
- [ ] Local model answers a question using retrieved passages.
- [ ] Answer includes a real source reference where available.
- [ ] Unsupported questions produce a clear uncertainty response.
- [ ] Checklist state persists after restart.
- [ ] User can remove a document and clear chat history.
- [ ] Model-unavailable and unreadable-document errors are understandable.

### Offline test
- [ ] Download the model and dependencies before testing.
- [ ] Disconnect Wi-Fi and disable other network connectivity.
- [ ] Restart the application.
- [ ] Ask a question about the bundled reference document.
- [ ] Confirm a local model generates the answer.
- [ ] Confirm source references still work.
- [ ] Confirm the checklist can be changed and saved.
- [ ] Confirm no cloud AI request is required for these functions.
- [ ] Record the test setup and result honestly.

### Demo quality
- [ ] Use a clean demo dataset.
- [ ] Prepare five tested questions.
- [ ] Ensure the model is downloaded and can start reliably.
- [ ] Prepare a fallback recording in case the live demo fails, without misrepresenting it as a live offline test.
- [ ] Capture evidence of the disconnected-network test.
- [ ] Keep the interface clean and free from debug output.

---

## 12. Hackathon Demo Plan

The supplied slides say the demo video should ideally be around one minute. The following is a recommended outline.

### 60-second demo storyboard

**0–8 seconds — The problem**
Show a scenario where a user needs emergency-preparedness information but has no internet connection.

**8–18 seconds — Open RescueDesk AI**
Show the local model ready state and a bundled emergency reference document.

**18–33 seconds — Ask a question**
Ask a question whose answer is explicitly in the guide. Show the generated answer and source reference.

**33–43 seconds — Verify the source**
Open the cited passage and compare it with the answer.

**43–52 seconds — Show preparedness checklist**
Mark an item complete and show the state saved locally.

**52–60 seconds — Prove Local AI**
Show the offline test evidence and explain that inference and core data processing happen on the user's device.

The recording and narration must accurately reflect the product's actual behavior. If the video is recorded while online, do not present it as proof of an offline test; perform and document a separate disconnected-network test.

---

## 13. Submission Checklist

The supplied competition slides specify these submission elements:

### Project details
- [ ] Project name: RescueDesk AI (working name; verify final name availability).
- [ ] Short description.
- [ ] Team members.
- [ ] Public GitHub repository.

### Proof
- [ ] Demo video, ideally around one minute.
- [ ] X or LinkedIn video post URL.
- [ ] Description of what runs locally.
- [ ] Description of what requires internet.

### Disclosures
- [ ] Models used, including version.
- [ ] Technologies and frameworks.
- [ ] APIs and cloud services, including a clear statement if none are used in the core app.
- [ ] Existing code and assets.
- [ ] AI development tools used.

### Required Local AI explanation
Answer directly:

**Why does this product benefit from running AI locally?**

Suggested draft, to be revised to match the implementation actually delivered:

> RescueDesk AI helps users consult emergency-preparedness documents when connectivity is unavailable. Running inference locally lets the core question-answering workflow continue without a cloud AI service and keeps imported documents on the user's device. Local processing is especially valuable when internet access is unreliable and when users do not want to upload personal preparedness plans or documents to a remote AI provider.

Do not claim that all functionality is fully offline until the end-to-end offline test has passed.

---

## 14. Recommended Build Order

Work in this order and do not move to later features while the core flow is broken.

1. **Confirm hardware and install local model runtime.** Run a basic local prompt before building the UI.
2. **Build the smallest end-to-end proof.** Load one trusted text document, retrieve a relevant passage, ask the local model, and show the answer.
3. **Add source references.** Ensure the reference points to real retrieved text.
4. **Add PDF extraction and document library.**
5. **Add the preparedness checklist and local persistence.**
6. **Build and polish the UI.**
7. **Test with internet disconnected.**
8. **Fix failures and record the demo.**
9. **Publish the public repository and complete all disclosures.**
10. **Submit before the deadline.**

If time becomes critically short, preserve this priority order:

1. Local inference that works.
2. Question answering grounded in a reference document.
3. Real source references.
4. Verified offline operation.
5. Basic checklist.
6. UI polish and optional features.

A polished interface cannot compensate for a core Local AI feature that does not work.

---

## 15. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Model too large or slow for the computer | High | Check hardware first; choose a smaller compatible model and test early. |
| Hallucinated or unsafe emergency advice | High | Use trusted source material, constrain answers to retrieved passages, display citations, and test unsupported questions. |
| Offline test fails | High | Avoid cloud dependencies in the core path; test with networking disabled well before recording. |
| PDF text extraction fails | Medium | Bundle a known-good text-based PDF and provide a plain-text fallback. |
| Scope expands | High | Freeze MVP scope around the P0 requirements. |
| Sources are outdated or redistribution is restricted | High | Track source dates, verify content and usage permissions, and show source attribution. |
| Demo computer differs from development computer | Medium | Test on the exact demo hardware whenever possible. |
| Model invents citations | High | Generate citations from retrieval metadata in application code, not from model-authored references. |

---

## 16. Success Metrics

For the hackathon MVP, use measurable pass/fail indicators rather than unsupported marketing claims.

- Core question-answering workflow succeeds in a disconnected-network test.
- Five predefined test questions are evaluated and documented.
- Correct source references are shown for supported questions.
- Unsupported questions are handled without confidently inventing an answer.
- Checklist state persists after restart.
- No cloud AI API is required for the core demo.
- Required submission information and disclosures are complete.
- Demo video is concise and accurately reflects the working build.

---

## 17. Decisions Still to Confirm

Before finalizing implementation, confirm:

1. **Development hardware:** operating system, RAM, available storage, and GPU/Apple Silicon details.
2. **Demo environment:** same computer or a separate machine.
3. **Model selection:** choose after checking hardware and testing latency.
4. **Reference documents:** select appropriate authoritative material and confirm usage permissions.
5. **Final product name:** RescueDesk AI is a working name.
6. **Repository and team details:** add the actual public GitHub URL and team members before submission.

These are implementation decisions, not reasons to delay building the initial local-inference proof.

---

## 18. Final Recommendation

RescueDesk AI should be a focused, offline-first emergency document assistant—not a full emergency management platform.

Its strongest competition argument is the combination of:
- A clear and socially useful problem.
- Local inference that is fundamental to the product.
- Private document processing.
- Answers tied to source passages.
- A demonstrable offline workflow.

Build the smallest version that proves those claims. Verify the behavior on the target computer, disclose all tools and models honestly, and prioritize reliability over feature count.
