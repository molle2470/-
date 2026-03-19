import { ScrollReveal } from '@/components/ui/ScrollReveal';

const categories = [
  {
    icon: (
      <svg
        className="w-6 h-6 text-primary"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <polyline points="16 18 22 12 16 6" />
        <polyline points="8 6 2 12 8 18" />
      </svg>
    ),
    title: '바이브코딩 튜토리얼',
    desc: '코딩을 몰라도 AI에게 말로 설명해서 웹사이트, 앱, 자동화 도구를 직접 만드는 방법을 알려드립니다.',
    tag: '인기 시리즈',
  },
  {
    icon: (
      <svg
        className="w-6 h-6 text-primary"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M12 2L2 7l10 5 10-5-10-5z" />
        <path d="M2 17l10 5 10-5" />
        <path d="M2 12l10 5 10-5" />
      </svg>
    ),
    title: 'Claude Code 마스터',
    desc: 'Claude Code를 200% 활용하는 팁과 트릭. 프롬프트 작성법부터 실제 프로젝트 빌딩까지 다룹니다.',
    tag: '심화 콘텐츠',
  },
  {
    icon: (
      <svg
        className="w-6 h-6 text-primary"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <circle cx="12" cy="12" r="3" />
        <path d="M12 1v6M12 17v6M4.22 4.22l4.24 4.24M15.54 15.54l4.24 4.24M1 12h6M17 12h6M4.22 19.78l4.24-4.24M15.54 8.46l4.24-4.24" />
      </svg>
    ),
    title: 'AI 생산성 자동화',
    desc: '반복 업무를 AI로 자동화하는 실전 가이드. 콘텐츠 생성, 데이터 처리, 워크플로우 자동화 등을 다룹니다.',
    tag: '실무 적용',
  },
];

export function CategoriesSection() {
  return (
    <section id="content" className="py-[120px] px-6 md:px-12 bg-[#FAFCFF]">
      <div className="max-w-[1100px] mx-auto text-center mb-16">
        <div className="text-[12px] font-bold uppercase tracking-[3px] text-primary mb-4">Content</div>
        <h2 className="text-[clamp(28px,4vw,42px)] font-bold tracking-[-0.04em] text-foreground leading-[1.2] mb-5">
          이런 콘텐츠를 만듭니다
        </h2>
        <p className="text-[16px] text-muted-foreground leading-[1.7] max-w-[560px] mx-auto">
          AI 초보부터 실무 활용까지, 단계별로 필요한 콘텐츠를 제공합니다.
        </p>
      </div>

      <div className="max-w-[1100px] mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
        {categories.map((cat, i) => (
          <ScrollReveal key={cat.title} delay={i * 100}>
            <div className="bg-white border border-primary/[0.08] rounded-[20px] p-10 hover:-translate-y-1.5 hover:shadow-[0_16px_48px_rgba(85,140,140,0.1)] hover:border-primary/[0.15] transition-all duration-300 h-full">
              <div className="w-12 h-12 bg-[#EFF7FF] rounded-[14px] flex items-center justify-center mb-6">
                {cat.icon}
              </div>
              <h3 className="text-[18px] font-bold mb-3 text-foreground">{cat.title}</h3>
              <p className="text-[14px] leading-[1.7] text-muted-foreground">{cat.desc}</p>
              <span className="inline-block mt-5 text-[12px] font-semibold text-primary bg-[#EFF7FF] px-3 py-1 rounded-full">
                {cat.tag}
              </span>
            </div>
          </ScrollReveal>
        ))}
      </div>
    </section>
  );
}
