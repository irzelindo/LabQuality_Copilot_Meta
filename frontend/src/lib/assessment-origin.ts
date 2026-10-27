export function assessmentOrigin(source: string, locale: string): string {
  const english = locale === "en";
  if (source.startsWith("odk:")) return english ? "Real · ODK" : "Real · ODK";
  if (source === "demo") return english ? "Simulated" : "Simulada";
  if (source === "manual") return english ? "Manual" : "Manual";
  return english ? "Imported" : "Importada";
}
