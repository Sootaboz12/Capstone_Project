import { Routes, Route } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import Landing from '../pages/Landing'
import MatchupPredictor from '../pages/Matchuppredictor'
import About from '../pages/About'
import Standings from '../pages/Standings'
import './App.css'

function App() {
  return (
    <div className="page">
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/predictor" element={<MatchupPredictor />} />
          <Route path="/standings" element={<Standings />} />
          <Route path="/about" element={<About />} />
          <Route path="*" element={<Landing />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}

export default App