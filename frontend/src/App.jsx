import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  const [pet, setPet] = useState(null)
  const [petResponse, setPetResponse] = useState(null)

  const getPet = async (petId) => {
    const response = await fetch(`http://localhost:8000/pets/${petId}`);
    const data = await response.json();
    setPet(data);
  }

  const chatWithPet = async (petId, message) => {
    const response = await fetch(`http://localhost:8000/pets/${petId}/chat`, {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    const data = await response.json();
    setPetResponse(data.message);
  }

  return (
    <>
      <h1>Pet Chat</h1>
      <div className="card">
        <h2>Select a pet to chat with</h2>
        <button onClick={() => getPet("1")}>
          Dog
        </button>
        <button onClick={() => getPet("2")}>
          Cat
        </button>
      </div>
      {pet && (
        <div>
          <h2>You are chatting with {pet.name}</h2>
          <input type="text" value={message} onChange={(e) => setMessage(e.target.value)} />
          <button onClick={() => chatWithPet(pet.id, message)}>
            Send
          </button>
        </div>
      )}
      {petResponse && (
        <div>
        Response: {petResponse}
        </div>
      )}
    </>
  );
}

export default App;
