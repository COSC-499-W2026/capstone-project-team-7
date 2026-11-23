# Week 11 Individual Log for Dan Rukundo

Team 7 | Lost In Translation | November 16–22, 2026

For Milestone 1 demo prep, I wrote French clues that make the difficulty levels feel different, added a way to keep playing when a location is impractical to reach, and connected the student audio player to the clue listen counter. All three PRs merged into `main` on November 22.

## French directions and story clues

- I wrote Advanced and Expert scripts for the five French demo rooms. Advanced clues give directions and state the room number. Expert clues use short stories to help students infer the number. For LIB 312, for example, the story combines the third floor with the twelve books a club reads in a year. Basic still uses room numbers only.
- I reused the existing audio generator and output paths. The tests check which script goes to each difficulty and verify that the Expert stories are distinct and omit the room number. After review, I removed the generated French clips from version control and documented how to regenerate them.
- The PR records 515 backend tests passed, with 339 skipped because a PostgreSQL test database was unavailable for that run, and 237 frontend tests passed. I generated all ten Advanced and Expert clips locally and verified that French hunts at both difficulties served the matching audio. [PR #261](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/261)

## Skip and replace a hunt location

- I added **Skip location** to the game screen. Students can skip before submitting a photo, and the game looks for an unused room with a clue in the hunt language, audio for its difficulty, and a GPS target. It replaces the current stop while keeping the hunt at five stops and preserving the timer and points. When no suitable room is available, the game keeps the current clue and shows a message.
- I added migration 017 to remember skipped rooms so they cannot come back in the same hunt. Backend tests cover successful replacement, stale skip requests, no available replacement, and keeping photo verification tied to the room that was actually checked.
- The PR records 856 backend tests passed against local PostgreSQL, 237 frontend tests passed, and a successful frontend build. In Chrome, I skipped the first room in a French Basic hunt before submitting a photo, played the replacement audio, and confirmed that the screen still showed **Spot 1 of 5** after reloading and resuming. I also checked the message when no spare room remained. [PR #263](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/263)

## Record plays from the student clue player

- I connected the student audio player to the listen counter from #248. The first playback and each replay after the clip ends count as separate plays. Pausing and resuming counts as one play, and audio continues if the tracking request fails.
- A skip can replace the clue while keeping the same spot number. I sent both the spot and the clue ID in the tracking request so the backend can reject a delayed request for the previous clue. Tests cover wrong-spot and wrong-clue requests and confirm that neither increments the count.
- The PR records 863 backend tests passed against local PostgreSQL, 237 frontend tests passed, and a successful frontend build. In Chrome, I checked first play, pause and resume, replay, and continued playback when tracking returned a 503. [PR #265](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/265)

## Code reviews

- I asked for badge progress to exclude teacher-added clues from both the total and found-location counts. I approved after checking the query changes and regression tests. I also agreed that the location-readiness filter should land first so hunts would only select rooms with usable audio. [Teacher locations #254](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/254#pullrequestreview-6007906023) · [Follow-up review](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/254#pullrequestreview-6008274359) · [Location readiness #258](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/258#pullrequestreview-6007881941)
- I suggested including the clue position when recording a listen so late requests could be checked. During debrief review, I found that replacing a room could carry its listen count over to the next room and make the debrief flag the wrong location. I asked for the skip update to reset listens alongside attempts and for a regression test on the completed hunt. [Listen counter #248](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/248#pullrequestreview-6007926463) · [Debrief data #269](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/269#pullrequestreview-6015581669)
- I also reviewed per-difficulty audio uploads, assigned-hunt completion, GPS hints, and the debrief screen. I flagged that the debrief API needed to merge ahead of the screen that uses it. [Audio uploads #252](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/252#pullrequestreview-6007913409) · [Assigned hunts #257](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/257#pullrequestreview-6007862529) · [GPS hints #267](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/267#pullrequestreview-6015577111) · [Debrief screen #271](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/271#pullrequestreview-6015589707)
