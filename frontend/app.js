(function () {
  const e = React.createElement;
  const rootEl = document.getElementById('root');

  const API_BASE = 'http://localhost:5000'; // backend base URL

  function App() {
    const [hello, setHello] = React.useState(null);
    const [items, setItems] = React.useState([]);
    const [postResult, setPostResult] = React.useState(null);

    React.useEffect(() => {
      fetch(`${API_BASE}/api/hello`)
        .then(r => r.json())
        .then(j => setHello(j.message))
        .catch(err => setHello('Error: ' + err.message));

      fetch(`${API_BASE}/api/data`)
        .then(r => r.json())
        .then(j => setItems(j.data || []))
        .catch(() => setItems([]));
    }, []);

    function sendSample() {
      fetch(`${API_BASE}/api/data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from: 'frontend', ts: Date.now() })
      })
      .then(r => r.json())
      .then(j => setPostResult(j))
      .catch(err => setPostResult({ error: err.message }));
    }

    return e('div', null,
      e('h1', null, 'React + Flask demo'),
      e('p', null, hello ? `Backend says: ${hello}` : 'Loading backend...'),
      e('h2', null, 'GET /api/data'),
      e('ul', null, items.map((it, idx) => e('li', { key: idx }, it))),
      e('h2', null, 'POST /api/data'),
      e('button', { onClick: sendSample }, 'Send sample POST'),
      postResult && e('div', { style: { marginTop: 12 } },
        e('strong', null, 'Response:'),
        e('pre', null, JSON.stringify(postResult, null, 2))
      )
    );
  }

  const root = ReactDOM.createRoot(rootEl);
  root.render(e(App));
})();
