const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function App() {
  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>AkarAI Agency</h1>
        <p style={styles.subtitle}>Dashboard &mdash; Manage Listings, Leads, and Viewings</p>
      </header>
      <main style={styles.main}>
        <div style={styles.grid}>
          <div style={styles.card}>
            <h3>Listings</h3>
            <p style={styles.count}>--</p>
          </div>
          <div style={styles.card}>
            <h3>Leads</h3>
            <p style={styles.count}>--</p>
          </div>
          <div style={styles.card}>
            <h3>Viewings</h3>
            <p style={styles.count}>--</p>
          </div>
        </div>
        <div style={styles.statusCard}>
          <span style={styles.badge}>Phase 1</span>
          <p>Infrastructure Ready &mdash; Backend: {API_BASE}</p>
        </div>
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: "100vh",
    backgroundColor: "#f1f5f9",
    fontFamily: "system-ui, -apple-system, sans-serif",
  },
  header: {
    backgroundColor: "#0f172a",
    color: "#fff",
    padding: "2rem",
    textAlign: "center",
  },
  title: {
    fontSize: "2rem",
    margin: 0,
    fontWeight: 700,
  },
  subtitle: {
    fontSize: "1rem",
    color: "#94a3b8",
    margin: "0.5rem 0 0",
  },
  main: {
    padding: "2rem",
    maxWidth: "800px",
    margin: "0 auto",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "1rem",
    marginBottom: "2rem",
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: "8px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
    padding: "1.5rem",
    textAlign: "center",
  },
  count: {
    fontSize: "2rem",
    fontWeight: 700,
    color: "#64748b",
    margin: "0.5rem 0 0",
  },
  statusCard: {
    backgroundColor: "#fff",
    borderRadius: "8px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
    padding: "1.5rem",
    textAlign: "center",
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
