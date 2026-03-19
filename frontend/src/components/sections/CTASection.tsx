const YOUTUBE_URL = 'https://www.youtube.com/@chacha';

export function CTASection() {
  return (
    <section className="py-[120px] px-6 md:px-12 bg-white">
      <div
        className="max-w-[900px] mx-auto rounded-[32px] py-20 px-8 md:px-16 text-center relative overflow-hidden"
        style={{ background: 'linear-gradient(135deg, #558C8C, #3D6B6B)' }}
      >
        {/* Decorations */}
        <div className="absolute -top-1/2 -right-[20%] w-[400px] h-[400px] rounded-full bg-white/[0.05] pointer-events-none" />
        <div className="absolute -bottom-[30%] -left-[10%] w-[300px] h-[300px] rounded-full bg-white/[0.04] pointer-events-none" />

        <div className="relative z-[1]">
          <h2 className="text-[clamp(28px,4vw,40px)] font-bold text-white tracking-[-0.03em] mb-4">
            AI 시대, 뒤처지지 마세요
          </h2>
          <p className="text-[16px] text-white/80 mb-10 leading-[1.6]">
            매주 올라오는 AI 실전 튜토리얼을 무료로 받아보세요.
            <br />
            구독 하나로 AI 생산성이 달라집니다.
          </p>
          <a
            href={YOUTUBE_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2.5 bg-white text-primary px-10 py-[18px] rounded-full font-bold text-[16px] hover:-translate-y-0.5 hover:shadow-[0_12px_40px_rgba(0,0,0,0.2)] transition-all duration-300"
          >
            무료 구독하기
            <svg
              className="w-5 h-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </a>
        </div>
      </div>
    </section>
  );
}
