export default function RecipeList({ recipes }) {
  return (
    <div>
      {recipes.length === 0 ? (
        <p>No recipes yet</p>
      ) : (
        recipes.map((r) => (
          <div key={r.id} style={{ border: "1px solid #ccc", margin: "10px", padding: "10px" }}>
            <h3>{r.title}</h3>
            <img src={r.image} alt={r.title} width="200" />
          </div>
        ))
      )}
    </div>
  );
}