import { ScrollReveal } from '@/components/ui/ScrollReveal';

const features = [
  {
    icon: (
      <svg
        className="w-5 h-5 text-primary"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
    ),
    title: '검증된 실전 경험',
    desc: '8년차 개발자 + AI 석사 출신이\n직접 실무에서 쓰는 방법만 공유',
  },
  {
    icon: (
      <svg
        className="w-5 h-5 text-primary"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
      </svg>
    ),
    title: '비개발자 눈높이',
    desc: '어려운 용어 없이\n누구나 따라할 수 있는 설명',
  },
  {
    icon: (
      <svg
        className="w-5 h-5 text-primary"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <circle cx="12" cy="12" r="10" />
        <line x1="2" y1="12" x2="22" y2="12" />
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
      </svg>
    ),
    title: '최신 AI 트렌드',
    desc: '빠르게 변하는 AI 도구와\n트렌드를 매주 업데이트',
  },
];

export function WhySection() {
  return (
    <section className="py-[120px] px-6 md:px-12 bg-[#EFF7FF] relative overflow-hidden">
      {/* Background decoration */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(circle, rgba(85,140,140,0.04), transparent 60%)' }}
      />

      <div className="max-w-[800px] mx-auto text-center relative z-[1]">
        <div className="text-[12px] font-bold uppercase tracking-[3px] text-primary mb-4">
          Why Subscribe
        </div>
        <h2 className="text-[clamp(28px,4vw,42px)] font-bold tracking-[-0.04em] text-foreground leading-[1.2]">
          왜 이 채널을 봐야 할까요?
        </h2>

        {/* Quote */}
        <div className="text-[clamp(22px,3vw,30px)] font-medium leading-[1.6] text-foreground my-10 relative">
          <span className="absolute -top-[60px] -left-5 text-[120px] text-primary opacity-[0.12] leading-[1] select-none">
            &ldquo;
          </span>
          코딩을 배우는 게 아니라,
          <br />
          AI에게{' '}
          <strong className="text-primary">시키는 방법</strong>을 배우는 겁니다.
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
          {features.map((feature, i) => (
            <ScrollReveal key={feature.title} delay={i * 100}>
              <div className="text-center">
                <div className="w-11 h-11 bg-white rounded-xl flex items-center justify-center mx-auto mb-4 shadow-[0_2px_12px_rgba(85,140,140,0.08)]">
                  {feature.icon}
                </div>
                <h4 className="text-[15px] font-bold text-foreground mb-2">{feature.title}</h4>
                <p className="text-[13px] text-muted-foreground leading-[1.6] whitespace-pre-line">
                  {feature.desc}
                </p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
