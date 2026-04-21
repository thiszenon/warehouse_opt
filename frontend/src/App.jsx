import { useState } from "react";
import MainLayout from "./layout/MainLayout";
import TourSelection from "./pages/TourSelection";
import Comparison from "./pages/Comparison";
import ExecutionPlan from "./pages/ExecutionPlan";
import { executionPlan } from "./data/executionPlan";

export default function App() {
  const [step, setStep] = useState(1);

  return (
    <MainLayout>
      {step === 1 && (
        <TourSelection onSelect={() => setStep(2)} />
      )}

      {step === 2 && (
        <Comparison
          onValidate={() => setStep(3)}
          onCancel={() => setStep(1)}
        />
      )}

      {step === 3 && (
        <ExecutionPlan
          plan={executionPlan}
          onBack={() => setStep(2)}
          onPrint={() => window.print()}
          onExport={() =>
            console.log("EXPORT DATA", executionPlan)
          }
        />
      )}
    </MainLayout>
  );
}
