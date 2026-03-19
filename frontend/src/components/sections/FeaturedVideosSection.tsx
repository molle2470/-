import { ScrollReveal } from '@/components/ui/ScrollReveal';

const YOUTUBE_URL = 'https://www.youtube.com/@chacha';

const videos = [
  {
    label: '튜토리얼',
    gradient: undefined,
    gradientStyle: { background: 'linear-gradient(135deg, #558C8C, #6FA8A8)' },
    title: '비개발자를 위한 바이브코딩 완전 가이드',
    desc: '코딩 경험 0인 분들을 위한 바이브코딩 입문 가이드. AI에게 말로 설명해서 웹사이트를 만드는 전 과정을 보여드립니다.',
    duration: '30분',
    audience: '입문자 추천',
  },
  {
    label: '실전',
    gradient: undefined,
    gradientStyle: { background: 'linear-gradient(135deg, #3D6B6B, #3D8B6B)' },
    title: 'Claude Code로 SaaS MVP 3일 만에 만들기',
    desc: '아이디어만 가지고 Claude Code를 활용해서 실제 운영 가능한 SaaS 서비스를 3일 안에 완성하는 과정을 담았습니다.',
    duration: '45분',
    audience: '실무자 추천',
  },
];

export function FeaturedVideosSection() {
  return (
    <section id="videos" className="py-[120px] px-6 md:px-12 bg-white">
      <div className="max-w-[1100px] mx-auto mb-16">
        <div className="text-[12px] font-bold uppercase tracking-[3px] text-primary mb-4">Featured</div>
        <h2 className="text-[clamp(28px,4vw,42px)] font-bold tracking-[-0.04em] text-foreground leading-[1.2] mb-5">
          인기 영상
        </h2>
        <p className="text-[16px] text-muted-foreground leading-[1.7]">
          가장 많은 분들이 봐주신 영상들입니다.
        </p>
      </div>

      <div className="max-w-[1100px] mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
        {videos.map((video, i) => (
          <ScrollReveal key={video.title} delay={i * 100}>
            <a
              href={YOUTUBE_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="group block rounded-[20px] overflow-hidden bg-[#FAFCFF] border border-primary/[0.06] hover:-translate-y-1 hover:shadow-[0_16px_48px_rgba(85,140,140,0.1)] transition-all duration-300"
            >
              {/* Thumbnail */}
              <div
                className="relative overflow-hidden"
                style={{ aspectRatio: '16/9', ...video.gradientStyle }}
              >
                <div className="absolute inset-0 bg-black/15" />

                {/* Label */}
                <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm px-3.5 py-1.5 rounded-lg text-[12px] font-semibold text-primary z-[2]">
                  {video.label}
                </div>

                {/* Play button */}
                <div className="absolute inset-0 flex items-center justify-center z-[2]">
                  <div className="w-14 h-14 bg-white/95 rounded-full flex items-center justify-center shadow-[0_4px_20px_rgba(0,0,0,0.15)] group-hover:scale-110 transition-transform duration-300">
                    <svg className="w-[22px] h-[22px] text-primary ml-0.5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  </div>
                </div>

                {/* Title overlay */}
                <div className="absolute bottom-0 left-0 right-0 px-6 pb-5 pt-8 bg-gradient-to-t from-black/60 to-transparent z-[2]">
                  <h4 className="text-[16px] font-bold text-white">{video.title}</h4>
                </div>
              </div>

              {/* Info */}
              <div className="p-6">
                <p className="text-[14px] text-muted-foreground leading-[1.6]">{video.desc}</p>
                <div className="flex items-center gap-4 mt-4">
                  <span className="text-[12px] text-muted-foreground flex items-center gap-1">
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" />
                      <polyline points="12 6 12 12 16 14" />
                    </svg>
                    {video.duration}
                  </span>
                  <span className="text-[12px] text-muted-foreground flex items-center gap-1">
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                    {video.audience}
                  </span>
                </div>
              </div>
            </a>
          </ScrollReveal>
        ))}
      </div>
    </section>
  );
}
