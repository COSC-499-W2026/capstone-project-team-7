### Week 7 — Madiba Burks Magara

October 19–25, 2026

Merged this week: [PR #136 — OCR foundation](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/136), into `main`. I also implemented and opened [PR #143 — Verify room photos and award points for correct targets](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/143) and [PR #145 — Connect live room photos to OCR verification](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/145). Both remain open at the time of writing and target `main`; the frontend depends on the verification backend.

PR sizes, merge status, reviews and CI results below were checked against GitHub while writing this log. Local test counts are recorded development runs from the relevant implementation snapshots, not new runs performed for this documentation. Generated-image recognition and synthetic-camera browser checks are identified separately from real-phone testing.

---

### For PR #136 — OCR foundation

- [x] The image-recognition requirement in [issue #103](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/103) needs a reusable way to read building and room identifiers from a student's photo. I added `extract_room_numbers()` in `src/backend/utils/ocr.py` using PaddleOCR and its CPU runtime.
- [x] I restricted recognised identifiers to the campus formats: UNC, FIP, COM, ASC, ART, CCS, ADM, SCI and LIB followed by a space and three digits; EME followed by four digits. Leading zeros are preserved, so `EME 0050` remains different from `EME 50`.
- [x] I normalised letters and whitespace, combined adjacent OCR text boxes, removed duplicate candidates and filtered out recognition scores below 0.8. Unknown building codes and incorrectly formatted room numbers are rejected.
- [x] I accepted JPEG/PNG photos up to 5 MiB and 20 million pixels, corrected image orientation from EXIF data, and cleaned up temporary images after processing. Invalid images raise `InvalidPhoto`; missing or failing OCR raises `OCRUnavailable`; no readable identifier returns an empty list.
- [x] I loaded the OCR engine only when needed and reused one instance per process. The foundation returns candidates without deciding whether a student has answered correctly or changing game points.
- [x] The merged change has 200 additions across five files, including tests and documentation. Pillow is in the base requirements; `requirements-ocr.txt` installs the existing backend requirements plus PaddleOCR and PaddlePaddle. No schema migration was needed.
- [x] Dan and Gamu approved the change. Gamu highlighted the need to confirm spaces versus dashes on actual campus signs and to test a real phone photo, because the recognition checks so far used generated images.
- [x] In the DFD, this supplies the image-recognition step between an uploaded photo and the backend's answer-verification process. It does not replace the separate GPS proximity check.

For Tests:

- [x] [`tests/backend/test_ocr.py` at `5a0bad9`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/5a0bad9/tests/backend/test_ocr.py) covers supported building codes, EME's four-digit format, leading zeros, case/whitespace normalisation, split text boxes, confidence filtering and duplicate removal.
- [x] Negative cases cover unsupported codes, incomplete or oversized identifiers, incorrect separators, empty/corrupt images, unsupported image formats, byte/pixel limits and OCR failures. Tests also check engine reuse and temporary-file cleanup.
- [x] The recorded foundation backend run passed **293 tests**, with **161 skipped** while database integration was disabled. The frontend run at that snapshot passed **9 tests**; these are not the later verification/frontend totals.
- [x] Real PaddleOCR recognised generated `LIB 308` and `EME 0050` images, and returned no candidates for a blank image. These checks establish that the runtime can recognise those examples, not that all real door signs will be recognised reliably.
- [x] GitHub reports successful [backend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40137341999/job/121001560075) and [frontend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40137341999/job/121001560222) for the merged PR head. The merge commit is `2b14e4d`.
- [ ] Real-phone checks on campus signs, including lighting, camera angles and separator formats, remain to be completed.

---

### For PR #143 — Verify room photos and award points for correct targets

- [x] For [issue #138](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/138), I replaced the temporary always-correct answer checker with a comparison between recognised identifiers and the student's current target. The full building and room must match; the expected answer comes from the database rather than the client.
- [x] I reused `POST /api/game/{game_id}/answer`, cookie-session authentication, student-role checks and game ownership checks. Invalid or oversized photos receive clear errors, and OCR/database failures return safe responses without internal details.
- [x] I awarded a flat 10 points for a correct location and zero for an incorrect or unreadable photo. Attempts are still recorded but do not reduce points. A correct answer advances the game, and the fifth correct location finishes it.
- [x] I made points, attempts and game progress commit together. The update checks the game owner, current position and unfinished state, so concurrent submissions cannot award the same location twice. A failed location update rolls back the points and progress update.
- [x] I added `007_photo_verification_points.sql` for persistent game points. I used 007 because Dan's merged GPS work already uses `006_location_coordinates.sql`; I did not rewrite that migration.
- [x] Review feedback on the earlier verification version identified that Docker did not install the optional OCR runtime. I updated the backend image to install the OCR requirements and native libraries, then fixed a Linux ARM inference crash using conservative CPU settings: MKL-DNN disabled and one CPU thread.
- [x] My first branch included unmerged dependency work and produced an oversized comparison. I rebuilt the change on `138-photo-verification-api-2` once the game and OCR dependencies were available in `main`. The final PR contains 156 additions and 44 deletions across eight files: 200 changed lines, with no new audio or seed files. It supersedes the closed dependency-based PR #141.
- [x] Dan approved the new PR. In the DFD, this connects photo recognition to the game-session process and SQL progress/points records; GPS verification remains separate from this acceptance decision.
- [ ] The PR remains open. Merge and deployment must happen before the frontend integration relies on its response fields.

For Tests:

- [x] [`tests/backend/test_answer_check.py` at `7677f8c`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/7677f8c/tests/backend/test_answer_check.py) checks matching LIB and EME targets, incorrect rooms/buildings, unreadable results, leading-zero mismatches and safe OCR errors. It checks that requests use the signed-in student's current target.
- [x] [`tests/backend/test_game_session.py`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/7677f8c/tests/backend/test_game_session.py) verifies positive scoring, zero-point retries and game completion. PostgreSQL cases check that concurrent correct submissions produce one success and one conflict, and that a failed location update leaves points and position unchanged.
- [x] The final backend suite passed **532 tests** against the rebuilt Docker image and an isolated PostgreSQL 17 database, including the existing GPS migration and the new points migration.
- [x] Real OCR inside Docker recognised generated `LIB 308` and `EME 0050` photos, returned no candidates for a blank image and rejected invalid bytes. These runtime checks were separate from the unit tests that fake recognition results.
- [x] The frontend suite at this snapshot passed **26 tests** in a clean installation using the existing lockfile. The original local install had two React hook failures; the clean-copy run avoided that dependency-resolution conflict without changing frontend files in this PR.
- [x] GitHub reports successful [backend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40214979217/job/121234050495) and [frontend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40214979217/job/121234050371) for the final PR head. These checks do not mean the open PR has been merged.

---

### For PR #145 — Connect live room photos to OCR verification

- [x] For [issue #144](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/144), I connected the existing live-camera page to the verification API through `src/frontend/src/api/answer.ts`. It sends the captured JPEG with the session cookie and displays the server's result.
- [x] I added a checking state, disabled submission/retake/close controls during a request, and guarded against duplicate clicks. Incorrect or unreadable photos keep the student on the photo page with zero awarded points and a retake option; upload, network and OCR failures allow retrying.
- [x] I added `VerificationResult.tsx` for correct-room feedback, awarded points, the game total and the final completion screen. After success, the student can load the next clue or return to the dashboard when the hunt is finished.
- [x] I kept scoring on the backend. The frontend displays returned points instead of calculating awards, and rejects incomplete or contradictory verification responses rather than presenting an unsupported success result.
- [x] I reused the existing camera capture, preview and cleanup flow, and updated the camera instruction to include both the building code and room number. No file-picker option or dependency was added.
- [x] The PR contains 154 additions and 10 deletions across seven files: 164 changed lines. It targets `main` directly and adds no backend, audio, seed or migration files.
- [x] Dan approved the connection. In the DFD, this completes the student's photo-to-API-to-feedback path while the backend remains responsible for verification, progress and points.
- [ ] The PR remains open and depends on #143 being merged and deployed first. Its browser checks do not establish a completed deployment of the combined system.

For Tests:

- [x] [`tests/frontend/answer.test.ts` at `f557222`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/f557222/tests/frontend/answer.test.ts) covers JPEG submission with session credentials, returned points, incorrect/unreadable results, expired sessions, oversized/invalid uploads, OCR/server/network failures and malformed responses.
- [x] Rendered-feedback cases check correct-room, zero-point and final-completion messages. The existing camera tests were updated for the new component props.
- [x] The frontend suite passed **41 tests** in a clean installation of the existing lockfile. `npm run build` also passed, including TypeScript checking and the Vite production build.
- [x] A headless browser with a synthetic camera and controlled API responses verified actual JPEG capture/upload, pending controls, duplicate-click prevention, zero-point feedback, retry after an OCR 503 response, next-clue navigation, the final 50-point result and return to the dashboard.
- [x] Those browser checks used simulated API responses, not a physical phone or the deployed OCR backend. GitHub separately reports successful [backend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40216540154/job/121238787046) and [frontend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40216540154/job/121238786749) for the PR head.

---

## How this fits the overall system

This work builds on the team's game sessions, current-clue/audio endpoints and live-camera page. The foundation reads candidate room identifiers; the verification API compares them with a server-owned target and records progress and points; the frontend explains the result and lets the student continue or retake the photo. The merged foundation and the two open integration PRs are separate delivery stages, rather than a claim that the whole flow is already deployed.

I also reviewed and approved Dan's [GPS proximity validation in #134](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/134), noting the clear migration, scoped validator and edge-case coverage. I approved [demo target coordinates in #137](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/137) with no requested edits, and [student profile access in #140](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/140), noting its student-role and ownership checks. These are review contributions, not claims that I reran those teammates' test suites.

Next steps are to merge and deploy #143 before #145, rebuild the backend image with OCR installed, and verify the combined flow on a real phone against campus signs. Model weights download on first use, so the demo environment needs a prepared cache or internet access. The team also needs to confirm sign separator formats, decide whether later scoring should depend on attempts or difficulty, and connect GPS proximity validation to answer acceptance. No application tests were rerun while writing this documentation.
