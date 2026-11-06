import type { Store } from '../api/store'
import ProfileIcon from './ProfileIcon'

interface Props {
  store: Store
  busy: boolean
  onBuy: (iconId: string) => void
  onEquip: (iconId: string) => void
}

const GRID = { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: 16, listStyle: 'none', padding: 0 }

// The coin balance and every icon, each with the right button: buy, need more coins, equip, or equipped.
export default function StoreView({ store, busy, onBuy, onEquip }: Props) {
  return (
    <>
      <p>You have {store.balance} coins</p>
      <ul style={GRID}>
        {store.icons.map((icon) => {
          const missing = icon.price === null ? 0 : icon.price - store.balance
          const locked = !icon.owned && (icon.price === null || missing > 0)
          return (
            <li key={icon.id}>
              <ProfileIcon id={icon.id} name={icon.name} size={96} locked={locked} />
              <p>{icon.name}<br />{icon.price === null ? 'Not for sale' : `${icon.price} coins`}</p>
              {icon.equipped ? <p>Equipped ✓</p>
                : icon.owned ? <button onClick={() => onEquip(icon.id)} disabled={busy}>Equip</button>
                : icon.price === null ? null
                : missing > 0 ? <button disabled>Need {missing} more coins</button>
                : <button onClick={() => onBuy(icon.id)} disabled={busy}>Buy for {icon.price} coins</button>}
            </li>
          )
        })}
      </ul>
    </>
  )
}
