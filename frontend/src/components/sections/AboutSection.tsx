import { ScrollReveal } from '@/components/ui/ScrollReveal';

const tags = ['Claude Code', '바이브코딩', 'AI 자동화', '실전 튜토리얼'];

export function AboutSection() {
  return (
    <section id="about" className="py-[120px] px-6 md:px-12 bg-white">
      <div className="max-w-[1100px] mx-auto grid grid-cols-1 md:grid-cols-2 gap-16 md:gap-[80px] items-center">
        {/* Content */}
        <ScrollReveal>
          <div className="text-[12px] font-bold uppercase tracking-[3px] text-primary mb-4">
            About Channel
          </div>
          <h2 className="text-[clamp(28px,4vw,42px)] font-bold tracking-[-0.04em] text-foreground leading-[1.2] mb-5">
            AI 시대,
            <br />
            실전 활용법을
            <br />
            알려드립니다
          </h2>
          <p className="text-[16px] text-muted-foreground leading-[1.7]">
            8년차 풀스택 개발자이자 AI 석사 출신.
            <br />
            코드 한 줄 모르는 분들도 AI로 서비스를 만들 수 있도록,
            <br />
            실전 위주의 튜토리얼과 노하우를 공유합니다.
          </p>
        </ScrollReveal>

        {/* Visual card */}
        <ScrollReveal delay={200}>
          <div className="bg-[#EFF7FF] rounded-3xl p-10 md:p-12 relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary to-primary-light" />
            <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center mb-6 shadow-[0_2px_12px_rgba(85,140,140,0.08)]">
              <svg
                className="w-7 h-7 text-primary"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 20h9" />
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
              </svg>
            </div>
            <h3 className="text-[20px] font-bold mb-3 text-foreground">바이브코딩 전문 채널</h3>
            <p className="text-[15px] leading-[1.7] text-muted-foreground">
              말로 설명하면 AI가 코드를 만들어주는 바이브코딩. 그 A to Z를 가장 쉽고 실전적으로
              알려드립니다.
            </p>
            <div className="flex flex-wrap gap-2 mt-5">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="bg-white border border-[#D8E8E8] px-3.5 py-1.5 rounded-full text-[13px] font-medium text-primary"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
