export type Difficulty = 'basic' | 'advanced' | 'expert'

export const DIFFICULTIES: [Difficulty, string][] = [['basic', 'Basic'], ['advanced', 'Advanced'], ['expert', 'Expert']]
export const DIFFICULTY_NAMES: Record<string, string> = Object.fromEntries(DIFFICULTIES)
