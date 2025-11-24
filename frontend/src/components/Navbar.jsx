import React from "react";
import { Link } from "react-router-dom";
import "../App.css";

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="nav-left">
        <Link to="/" className="brand">📰 NewsPrep 2.0</Link>
      </div>
      <div className="nav-right">
        <Link to="/">Topics</Link>
        <a href="/search">Search</a>
        <Link to="/chat">Chat</Link>


      </div>
    </nav>
  );
}
