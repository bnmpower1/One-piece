import { useState } from 'react'
import './App.css'

type PriceData = {
  card_name: string
  card_number: string
  set: string
  rarity: string
  variant: string
  image_url: string
  prices: Record<string, number>
  currency: string
}

type SuggestionData = {
  suggestion: 'buy' | 'hold' | 'sell'
  reasoning: string
  card_name: string
  card_number: string
  rarity: string
  image_url: string
  avg_price_usd: number
}

type ApiResponse<T> = {
  status: string
  data?: T | string[]
  message?: string
}

export default function App() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [priceResult, setPriceResult] = useState<ApiResponse<PriceData> | null>(null)
  const [suggestionResult, setSuggestionResult] = useState<ApiResponse<SuggestionData> | null>(null)

  async function search(e: React.FormEvent) {
    e.preventDefault()
    const q = query.trim()
    if (!q) return

    setLoading(true)
    setPriceResult(null)
    setSuggestionResult(null)

    const encoded = encodeURIComponent(q)
    const [priceRes, suggestRes] = await Promise.allSettled([
      fetch(`/api/cards/price?q=${encoded}`).then(r => r.json()),
      fetch(`/api/cards/suggest?q=${encoded}`).then(r => r.json()),
    ])

    if (priceRes.status === 'fulfilled') setPriceResult(priceRes.value)
    if (suggestRes.status === 'fulfilled') setSuggestionResult(suggestRes.value)
    setLoading(false)
  }

  function searchFor(term: string) {
    setQuery(term)
    setLoading(true)
    setPriceResult(null)
    setSuggestionResult(null)

    const encoded = encodeURIComponent(term)
    Promise.allSettled([
      fetch(`/api/cards/price?q=${encoded}`).then(r => r.json()),
      fetch(`/api/cards/suggest?q=${encoded}`).then(r => r.json()),
    ]).then(([priceRes, suggestRes]) => {
      if (priceRes.status === 'fulfilled') setPriceResult(priceRes.value)
      if (suggestRes.status === 'fulfilled') setSuggestionResult(suggestRes.value)
      setLoading(false)
    })
  }

  const priceData = priceResult?.status === 'success' ? (priceResult.data as PriceData) : null
  const suggestData = suggestionResult?.status === 'success' ? (suggestionResult.data as SuggestionData) : null
  const multipleMatches = priceResult?.status === 'multiple_matches' ? (priceResult.data as string[]) : null

  return (
    <div className="app">
      <header>
        <h1>One Piece Card Tracker</h1>
        <p>Search by card number, name, or set code</p>
      </header>

      <form onSubmit={search} className="search-form">
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="e.g. OP06-118  ·  Zoro  ·  manga shanks"
          className="search-input"
        />
        <button type="submit" disabled={loading} className="search-btn">
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>

      {priceResult?.status === 'not_found' && (
        <p className="notice error">No card found for "{query}".</p>
      )}

      {multipleMatches && (
        <div className="matches">
          <p>Multiple cards matched — pick one:</p>
          <ul>
            {multipleMatches.map(m => (
              <li key={m}>
                <button onClick={() => searchFor(m.split(' ')[0])} className="match-btn">
                  {m}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {priceData && (
        <div className="card">
          {priceData.image_url && (
            <img
              src={`/api/cards/image?url=${encodeURIComponent(priceData.image_url)}`}
              alt={priceData.card_name}
              className="card-image"
            />
          )}

          <div className="card-info">
            <div>
              <h2>{priceData.card_name}</h2>
              <p className="card-meta">
                {priceData.card_number} · {priceData.set} · {priceData.rarity}
              </p>
              {priceData.variant !== 'Standard' && (
                <span className="variant-badge">{priceData.variant}</span>
              )}
            </div>

            <div className="prices">
              {Object.entries(priceData.prices).map(([source, price]) => (
                <div key={source} className="price-row">
                  <span className="price-source">{source}</span>
                  <span className="price-value">${price.toFixed(2)}</span>
                </div>
              ))}
            </div>

            {suggestData ? (
              <div className={`suggestion suggestion-${suggestData.suggestion}`}>
                <span className="suggestion-label">{suggestData.suggestion.toUpperCase()}</span>
                <p className="suggestion-reasoning">{suggestData.reasoning}</p>
              </div>
            ) : !loading && suggestionResult?.status === 'insufficient_data' ? (
              <p className="notice">No suggestion available for this card.</p>
            ) : null}
          </div>
        </div>
      )}
    </div>
  )
}
