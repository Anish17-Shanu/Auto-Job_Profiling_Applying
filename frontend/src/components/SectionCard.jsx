export function SectionCard({ title, children, actions }) {
  return (
    <section className="section-card">
      <div className="section-card-header">
        <h2>{title}</h2>
        {actions ? <div>{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}

