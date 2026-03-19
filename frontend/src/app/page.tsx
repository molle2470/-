import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';
import { HeroSection } from '@/components/sections/HeroSection';
import { AboutSection } from '@/components/sections/AboutSection';
import { CategoriesSection } from '@/components/sections/CategoriesSection';
import { FeaturedVideosSection } from '@/components/sections/FeaturedVideosSection';
import { WhySection } from '@/components/sections/WhySection';
import { CTASection } from '@/components/sections/CTASection';

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main>
        <HeroSection />
        <AboutSection />
        <CategoriesSection />
        <FeaturedVideosSection />
        <WhySection />
        <CTASection />
      </main>
      <Footer />
    </>
  );
}
