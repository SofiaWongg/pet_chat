import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  const [pet, setPet] = useState(null)

  return (
    <>
      <h1>Pet Chat</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          Chat with Pet
        </button>
      </div>
    </>
  )
}

export default App
