import { Navbar } from "@/components/landing/Navbar";
import { CinematicHero } from "@/components/landing/CinematicHero";
import { DiscrepancyReveal } from "@/components/landing/DiscrepancyReveal";
import { SystemArchitectureFlow } from "@/components/landing/SystemArchitectureFlow";
import { CoreThesisStory } from "@/components/landing/CoreThesisStory";
import { InvestigatorExperience } from "@/components/landing/InvestigatorExperience";
import { AuthorizationFirewall } from "@/components/landing/AuthorizationFirewall";
import { BenchmarkReport } from "@/components/landing/BenchmarkReport";
import { ScenarioChronicle } from "@/components/landing/ScenarioChronicle";
import { ConfidenceCalibration } from "@/components/landing/ConfidenceCalibration";
import { SafetyConstitution } from "@/components/landing/SafetyConstitution";
import { CinematicCta } from "@/components/landing/CinematicCta";
import { CinematicFooter } from "@/components/landing/CinematicFooter";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#F3F0E8] text-[#171816] selection:bg-[#A47C52]/25 selection:text-[#171816]">
      <Navbar />
      <main>
        <CinematicHero />
        <DiscrepancyReveal />
        <SystemArchitectureFlow />
        <CoreThesisStory />
        <InvestigatorExperience />
        <AuthorizationFirewall />
        <BenchmarkReport />
        <ScenarioChronicle />
        <ConfidenceCalibration />
        <SafetyConstitution />
        <CinematicCta />
      </main>
      <CinematicFooter />
    </div>
  );
}
