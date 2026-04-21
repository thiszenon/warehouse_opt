export default function ExecutionPlan({ plan, onBack, onPrint, onExport }) {
  return (
    <div className="print-preview">

      {/* En-tête */}
      <div className="print-header">
        <h2>TÂCHES DE PICKING</h2>
        <div>
          <strong>Tournée :</strong> {plan.tourId}
          <span style={{ marginLeft: 24 }}>
            <strong>Date :</strong> {plan.date}
          </span>
        </div>
      </div>

      {/* Liste des tâches */}
      <div className="tasks">
        {plan.tasks.map(task => (
          <div key={task.routeOrder} className="task-row">

            {/* Ordre de parcours */}
            <div className="task-order">
              {task.routeOrder.toString().padStart(2, "0")}
            </div>

            {/* Infos article */}
            <div className="task-info">
              <div className="main-line">
                <strong>{task.location}</strong> | {task.articleCode} | Qté:{task.quantity} {task.jobLink}
              </div>

              <div className="sub-line">
                [ BARCODE ARTICLE ]
              </div>

              <div className="sub-line">
                Réf:{task.reference} &nbsp; Stock:{task.stock}
              </div>
            </div>

            {/* Étiquette de contrôle */}
            <div className="task-label">
              <div><strong>{plan.tourId} - {task.routeOrder}</strong></div>
              <div>{task.location}</div>
              <div>{task.articleCode}</div>
              <div>Qté:{task.quantity}</div>
              <div>[ BARCODE ]</div>
            </div>

          </div>
        ))}
      </div>

      {/* Pied de page */}
      <div className="print-footer">
        <div>Préparateur : ______________________</div>
        <div className="produced">Produced by Picking Optimizer</div>
      </div>

      {/* Actions (non imprimées) */}
      <div className="actions no-print">
        <button onClick={onPrint}>Imprimer</button>
        <button onClick={onExport}>Exporter les données</button>
        <button onClick={onBack}>Retour</button>
      </div>

    </div>
  );
}