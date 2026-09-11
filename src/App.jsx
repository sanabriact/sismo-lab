import './App.css'
import Header from './layout/static/Header'
import Sidebar from './layout/static/Sidebar'
import Footer from './layout/static/Footer'

function App() {
  return (
    <>
      <div id="header">
        <Header></Header>
      </div>
      <section id="sidebar">
        <Sidebar></Sidebar>
      </section>
      <section id="footer">
        <Footer></Footer>
      </section>
    </>
  )
}

export default App