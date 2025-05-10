import React from 'react'
import { useRouteSocket } from './hooks/useRouteSocket'
import { useChatSocket } from './hooks/useChatSocket'
import { Chat } from './components/Chat'

function App() {
  const route = useRouteSocket()
  const { messages, sendMessage } = useChatSocket()

  // Calculate % time saved if route data is available
  let pctSaved = null
  if (route) {
    const { baseline_eta, optimized_eta } = route
    pctSaved = ((baseline_eta - optimized_eta) / baseline_eta) * 100
  }

  return (
    <div className="min-h-screen bg-gray-100 text-black p-4 font-sans">
      <h1 className="text-3xl font-bold mb-4">TransitEdge: Route Monitor</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white p-4 rounded shadow">
          <h2 className="text-xl font-semibold mb-2">Latest Route Data:</h2>
          {route ? (
            <pre className="whitespace-pre-wrap">{JSON.stringify(route, null, 2)}</pre>
          ) : (
            <p className="text-gray-500">Waiting for live route data...</p>
          )}
        </div>

        <div>
          <Chat messages={messages} sendMessage={sendMessage} />
        </div>
      </div>
    </div>
  )
}

export default App