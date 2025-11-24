import React from "react";

export function SearchBar({ onSearch, placeholder = "Search..." }) {
  const [q, setQ] = React.useState("");

  const submit = (e) => {
    e.preventDefault();
    if (onSearch) onSearch(q);
  };

  return (
    <form className="search" onSubmit={submit}>
      <input
        placeholder={placeholder}
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <button type="submit">Go</button>
    </form>
  );
}
