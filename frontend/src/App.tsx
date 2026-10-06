import { useEffect, useState } from "react";
import { Icon } from "./Icon";

export default function App() {
  const [status, setStatus] = useState("loading...");

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((d) => setStatus(d.status))
      .catch(() => setStatus("backend unreachable"));
  }, []);

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold">App</h1>
      <p className="mt-2 flex items-center gap-1">
        {status === "ok" ? (
          <Icon name="check_circle" className="text-green-600" />
        ) : (
          <Icon name="error" className="text-red-600" />
        )}{" "}
        API status: {status}
      </p>
    </main>
  );
}
