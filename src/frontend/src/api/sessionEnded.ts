// Thrown when the backend says the login session has ended (401), so the app can show the login page again.

export class SessionEndedError extends Error {
  constructor() {
    super('Please log in again')
    this.name = 'SessionEndedError'
  }
}
