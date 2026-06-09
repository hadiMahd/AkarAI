const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function App() {
  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>AkarAI</h1>
        <p style={styles.subtitle}>Find Your Home in Lebanon</p>
      </header>
      <main style={styles.main}>
        <div style={styles.statusCard}>
          <span style={styles.badge}>Phase 1</span>
          <h2>Infrastructure Ready</h2>
          <p>Backend API: {API_BASE}</p>
        </div>
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: "100vh",
    backgroundColor: "#f8fafc",
    fontFamily: "system-ui, -apple-system, sans-serif",
  },
  header: {
    backgroundColor: "#1e293b",
    color: "#fff",
    padding: "2rem",
    textAlign: "center",
  },
  title: {
    fontSize: "2.5rem",
    margin: 0,
    fontWeight: 700,
  },
  subtitle: {
    fontSize: "1.1rem",
    color: "#94a3b8",
    margin: "0.5rem 0 0",
  },
  main: {
    display: "flex",
    justifyContent: "center",
    padding: "2rem",
  },
  statusCard: {
    backgroundColor: "#fff",
    borderRadius: "8px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
    padding: "2rem",
    textAlign: "center",
    maxWidth: "400px",
    width: "100%",
  },
  badge: {
    backgroundColor: "#22c55e",
    color: "#fff",
    fontSize: "0.75rem",
    fontWeight: 600,
    padding: "0.25rem 0.75rem",
    borderRadius: "999px",
  },
};

export default App;
