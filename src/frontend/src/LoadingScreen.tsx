import './LoadingScreen.css'

interface LoadingScreenProps {
  progress: number
}

// Order matters: each sticker's spot on screen comes from its number in LoadingScreen.css
const STICKERS = [
  { word: 'Bonjour', icon: 'french', color: 'var(--yellow)' },
  { word: 'Hola', icon: 'spanish', color: 'var(--pink)' },
  { word: 'Salut', icon: 'french', color: 'var(--sky)', small: true },
  { word: '您好', icon: 'chinese', color: 'var(--lime)', small: true },
  { word: '你好', icon: 'chinese', color: 'var(--teal)' },
  { word: 'Buenas', icon: 'spanish', color: 'var(--yellow)', small: true },
  { word: 'Guten Tag', icon: 'german', color: 'var(--pink)', small: true },
  { word: 'こんにちは', icon: 'japanese', color: 'var(--sky)' },
  { word: 'おはよう', icon: 'japanese', color: 'var(--orange)', small: true },
  { word: '안녕', icon: 'korean', color: 'var(--lime)' },
  { word: '안녕하세요', icon: 'korean', color: 'var(--teal)', small: true },
  { word: 'Hallo', icon: 'german', color: 'var(--orange)' },
]

export default function LoadingScreen({ progress }: LoadingScreenProps) {
  return (
    <main className="loading-screen">
      {STICKERS.map((sticker, index) => (
        <div
          key={sticker.word}
          className={`sticker sticker--${index + 1} ${sticker.small ? 'sticker--small' : ''}`}
          style={{ background: sticker.color }}
          aria-hidden="true"
        >
          <img src={`/icons/${sticker.icon}.svg`} alt="" width={30} height={30} />
          {sticker.word}
        </div>
      ))}

      <div className="loading-logo">
        <img src="/icons/logo.svg" alt="" width={72} height={72} />
      </div>

      <h1 className="loading-title">
        Lost In <span>Translation</span>
      </h1>

      <div
        className="loading-bar"
        role="progressbar"
        aria-label="Loading"
        aria-valuenow={progress}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className="loading-bar-fill" style={{ width: `${progress}%` }} />
      </div>
      <p className="loading-text">Packing your clues...</p>
    </main>
  )
}