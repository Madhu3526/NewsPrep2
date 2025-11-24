import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import TopicList from "./pages/TopicList";
import TopicDetail from "./pages/TopicDetail";
import Explore from "./pages/Explore";
import Search from "./pages/Search";   // <-- FIXED
import "./App.css";
import QuizPage from "./pages/Quiz";
import AskPage from "./pages/Ask";
import Chat from "./pages/Chat";



export default function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<TopicList />} />
  <Route path="/topic/:id" element={<TopicDetail />} />
  <Route path="/explore" element={<Explore />} />
  <Route path="/explore/:id" element={<Explore />} />
<Route path="/quiz/:quiz_id" element={<QuizPage />} />
<Route path="/ask" element={<AskPage />} />
<Route path="/chat" element={<Chat />} />


        <Route path="/search" element={<Search />} /> {/* <-- WORKS */}
      </Routes>
    </Router>
  );
}
