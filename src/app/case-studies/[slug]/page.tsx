import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { CaseStudyDetail } from "@/components/CaseStudyDetail";
import { FactoryTransformationCaseStudyDetail } from "@/components/FactoryTransformationCaseStudyDetail";
import { caseStudies, getCaseStudy } from "@/data/caseStudies";
import {
  factoryTransformationCaseStudies,
  getFactoryTransformationCaseStudy,
} from "@/data/factoryTransformationCaseStudies";

type CasePageProps = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return [...caseStudies, ...factoryTransformationCaseStudies].map(
    (caseStudy) => ({ slug: caseStudy.slug }),
  );
}

export async function generateMetadata({ params }: CasePageProps): Promise<Metadata> {
  const { slug } = await params;
  const factoryTransformationCaseStudy =
    getFactoryTransformationCaseStudy(slug);

  if (factoryTransformationCaseStudy) {
    return {
      title: `${factoryTransformationCaseStudy.title.en} | Felix Zuo`,
      description: factoryTransformationCaseStudy.subtitle.en,
    };
  }

  const caseStudy = getCaseStudy(slug);

  if (!caseStudy) {
    return {
      title: "Case study not found | Felix Zuo",
    };
  }

  return {
    title: `${caseStudy.title} | Felix Zuo`,
    description: caseStudy.subtitle,
  };
}

export default async function CaseStudyPage({ params }: CasePageProps) {
  const { slug } = await params;
  const factoryTransformationCaseStudy =
    getFactoryTransformationCaseStudy(slug);

  if (factoryTransformationCaseStudy) {
    return (
      <FactoryTransformationCaseStudyDetail
        caseStudy={factoryTransformationCaseStudy}
      />
    );
  }

  const caseStudy = getCaseStudy(slug);

  if (!caseStudy) {
    notFound();
  }

  return <CaseStudyDetail caseStudy={caseStudy} />;
}

