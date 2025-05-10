import React from 'react'
import { useRouteSocket } from './hooks/useRouteSocket'
import { useChatSocket } from './hooks/useChatSocket'
import { Chat } from './components/Chat'

function App() {
  const { routeData, connected: routeConnected } = useRouteSocket()
  const { messages, sendMessage, connected: chatConnected } = useChatSocket()

  // Calculate % time saved if route data is available
  let pctSaved = null
  if (routeData) {
    const { baseline_eta, optimized_eta } = routeData
    pctSaved = ((baseline_eta - optimized_eta) / baseline_eta) * 100
  }

  return (
    <div className="min-h-screen bg-gray-100 text-black p-4 font-sans">
      <h1 className="text-3xl font-bold mb-4">TransitEdge: Route Monitor</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white p-4 rounded shadow">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-xl font-semibold">Latest Route Data</h2>
            <span className={`px-2 py-1 rounded text-sm ${routeConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              {routeConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          {routeData ? (
            <pre className="whitespace-pre-wrap">{JSON.stringify(routeData, null, 2)}</pre>
          ) : (
            <p className="text-gray-500">Waiting for live route data...</p>
          )}
        </div>

        <div className="bg-white p-4 rounded shadow">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-xl font-semibold">Chat</h2>
            <span className={`px-2 py-1 rounded text-sm ${chatConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              {chatConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <Chat messages={messages} sendMessage={sendMessage} />
        </div>
      </div>
    </div>
  )
}

export default App