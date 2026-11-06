import { useEffect, useRef, useState } from 'react'
import { SessionEndedError } from '../api/sessionEnded'
import { equipIcon, getStore, redeemIcon, type Store } from '../api/store'
import StoreView from '../components/StoreView'

interface Props {
  onBack: () => void
  onSessionEnded: () => void
}

export default function StorePage({ onBack, onSessionEnded }: Props) {
  const [store, setStore] = useState<Store | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  // A ref updates straight away, so a fast double click can't send two requests.
  const inFlight = useRef(false)

  function showError(err: unknown) {
    if (err instanceof SessionEndedError) onSessionEnded()
    else setError((err as Error).message)
  }

  useEffect(() => {
    getStore().then(setStore).catch(showError)
  }, [])

  // Buy or equip, then reload the store so the coins and buttons are up to date.
  async function run(action: () => Promise<void>) {
    if (inFlight.current) return
    inFlight.current = true
    setError('')
    setBusy(true)
    try {
      await action()
      setStore(await getStore())
    } catch (err) {
      showError(err)
    } finally {
      inFlight.current = false
      setBusy(false)
    }
  }

  return (
    <main>
      <h1>Store</h1>
      <button onClick={onBack} disabled={busy}>Back</button>
      {error && <p role="alert">{error}</p>}
      {store
        ? <StoreView store={store} busy={busy} onBuy={(id) => run(() => redeemIcon(id))} onEquip={(id) => run(() => equipIcon(id))} />
        : !error && <p>Loading store...</p>}
    </main>
  )
}
