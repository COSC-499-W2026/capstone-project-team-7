import { useEffect, useState } from "react";

interface HelloResponse {
  message: string;
}

export default function App() {
  const [message, setMessage] = useState("Loading...");

  useEffect(() => {
    fetch("/api/hello")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<HelloResponse>;
      })
      .then((data) => setMessage(data.message))
      .catch((err: Error) => setMessage(`Could not reach backend: ${err.message}`));
  }, []);

  return <h1>{message}</h1>;
}
