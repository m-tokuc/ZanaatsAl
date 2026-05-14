import os
import json
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

class MarketResearchAgent:
    """
    Otonom Market Research Agent - Serper.dev API ile Google araması yapar
    Etsy ve Amazon odaklı pazar araştırması gerçekleştirir
    """
    
    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        if not self.serper_api_key:
            raise ValueError("SERPER_API_KEY bulunamadı! .env dosyasını kontrol edin.")
        
        self.base_url = "https://google.serper.dev/search"
        self.headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }
    
    def search_etsy_products(self, keywords: List[str], num_results: int = 10) -> Dict:
        """
        Etsy'de ürün araması yapar
        """
        # Türkçe kelimeleri İngilizce'ye çevir
        english_keywords = self._translate_keywords(keywords)
        search_query = " ".join(english_keywords) + " site:etsy.com"
        return self._perform_search(search_query, num_results, "Etsy")
    
    def search_amazon_products(self, keywords: List[str], num_results: int = 10) -> Dict:
        """
        Amazon'da ürün araması yapar
        """
        # Türkçe kelimeleri İngilizce'ye çevir
        english_keywords = self._translate_keywords(keywords)
        search_query = " ".join(english_keywords) + " site:amazon.com"
        return self._perform_search(search_query, num_results, "Amazon")
    
    def search_competitor_prices(self, keywords: List[str]) -> Dict:
        """
        Rakip fiyatlarını araştırır
        """
        price_query = " ".join(keywords) + " fiyat price cost"
        return self._perform_search(price_query, 15, "Fiyat Analizi")
    
    def search_customer_reviews(self, keywords: List[str]) -> Dict:
        """
        Müşteri yorumlarını ve şikayetleri araştırır (İngilizce odaklı)
        """
        # Türkçe kelimeleri İngilizce'ye çevir
        english_keywords = self._translate_keywords(keywords)
        
        # İngilizce odaklı arama sorguları
        review_queries = [
            " ".join(english_keywords) + " reviews rating feedback",
            " ".join(english_keywords) + " customer experience opinion",
            " ".join(english_keywords) + " pros cons advantages disadvantages",
            " ".join(english_keywords) + " user experience testimonials"
        ]
        
        all_results = []
        
        for query in review_queries:
            result = self._perform_search(query, 5, "Müşteri Yorumları")
            if result.get('results'):
                all_results.extend(result['results'])
        
        # Tekrarları kaldır ve sonuçları birleştir
        unique_results = []
        seen_links = set()
        
        for result in all_results:
            if result.get('link') not in seen_links:
                unique_results.append(result)
                seen_links.add(result.get('link'))
        
        return {
            'search_type': 'Müşteri Yorumları',
            'query': ' + '.join(review_queries),
            'results': unique_results[:15],  # İlk 15 benzersiz sonuç
            'total_results': len(unique_results)
        }
    
    def _perform_search(self, query: str, num_results: int, search_type: str) -> Dict:
        """
        Google araması gerçekleştirir
        """
        payload = {
            'q': query,
            'num': num_results,
            'gl': 'us',  # USA için
            'hl': 'en'   # İngilizce sonuçlar
        }
        
        try:
            print(f"🔍 {search_type} araması yapılıyor: {query}")
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload
            )
            
            response.raise_for_status()
            data = response.json()
            
            print(f"✅ {search_type} araması başarılı! {len(data.get('organic', []))} sonuç bulundu.")
            
            return {
                'search_type': search_type,
                'query': query,
                'results': data.get('organic', []),
                'total_results': len(data.get('organic', [])),
                'related_searches': data.get('relatedSearches', [])
            }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ {search_type} araması hatası: {str(e)}")
            return {
                'search_type': search_type,
                'query': query,
                'results': [],
                'total_results': 0,
                'error': str(e)
            }
    
    def extract_price_from_text(self, text: str) -> Optional[float]:
        """
        Metinden fiyat bilgisi çıkarır
        """
        # Fiyat patternleri: $12.99, 12.99 USD, €12.99, TL 12.99
        price_patterns = [
            r'\$(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*USD',
            r'€(\d+\.?\d*)',
            r'TL\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*TL'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    price = float(match.group(1))
                    return price
                except ValueError:
                    continue
        
        return None
    
    def analyze_competitor_data(self, keywords: List[str]) -> Dict:
        """
        Tam pazar araştırması analizi
        """
        print("🚀 Market Research Agent başlatılıyor...")
        print("=" * 60)
        
        # Paralel aramalar yap
        etsy_results = self.search_etsy_products(keywords)
        amazon_results = self.search_amazon_products(keywords)
        price_results = self.search_competitor_prices(keywords)
        review_results = self.search_customer_reviews(keywords)
        
        # Fiyat analizi
        all_prices = []
        
        # Etsy fiyatları
        for result in etsy_results.get('results', []):
            price = self.extract_price_from_text(result.get('snippet', '') + result.get('title', ''))
            if price:
                all_prices.append({'source': 'Etsy', 'price': price, 'title': result.get('title', '')})
        
        # Amazon fiyatları
        for result in amazon_results.get('results', []):
            price = self.extract_price_from_text(result.get('snippet', '') + result.get('title', ''))
            if price:
                all_prices.append({'source': 'Amazon', 'price': price, 'title': result.get('title', '')})
        
        # İstatistiksel analiz
        if all_prices:
            prices = [item['price'] for item in all_prices]
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            
            price_analysis = {
                'average_price': round(avg_price, 2),
                'min_price': min_price,
                'max_price': max_price,
                'price_range': max_price - min_price,
                'total_products_analyzed': len(all_prices),
                'price_samples': all_prices[:10]  # İlk 10 örnek
            }
        else:
            price_analysis = {
                'error': 'Fiyat bilgisi bulunamadı'
            }
        
        # Yorum analizi
        review_summary = self._analyze_reviews(review_results)
        
        # Nihai rapor
        market_report = {
            'keywords_analyzed': keywords,
            'etsy_results': {
                'total_found': etsy_results.get('total_results', 0),
                'top_products': etsy_results.get('results', [])[:5]
            },
            'amazon_results': {
                'total_found': amazon_results.get('total_results', 0),
                'top_products': amazon_results.get('results', [])[:5]
            },
            'price_analysis': price_analysis,
            'customer_insights': review_summary,
            'research_timestamp': self._get_timestamp()
        }
        
        print("🎯 Market Research Agent analizi tamamlandı!")
        return market_report
    
    def _analyze_reviews(self, review_results: Dict) -> Dict:
        """
        Müşteri yorumlarını analiz eder
        """
        reviews = review_results.get('results', [])
        
        if not reviews:
            return {'error': 'Yorum bulunamadı'}
        
        # Basit sentiment analizi (kelime tabanlı)
        positive_words = ['good', 'great', 'excellent', 'perfect', 'love', 'amazing', 'quality', 'recommend']
        negative_words = ['bad', 'poor', 'terrible', 'disappointed', 'waste', 'broken', 'cheap', 'problem']
        
        positive_count = 0
        negative_count = 0
        
        review_snippets = []
        
        for review in reviews[:10]:  # İlk 10 yorum
            snippet = review.get('snippet', '').lower()
            title = review.get('title', '').lower()
            combined_text = snippet + ' ' + title
            
            # Positive kelimeleri say
            pos_found = sum(1 for word in positive_words if word in combined_text)
            neg_found = sum(1 for word in negative_words if word in combined_text)
            
            if pos_found > neg_found:
                positive_count += 1
            elif neg_found > pos_found:
                negative_count += 1
            
            review_snippets.append({
                'title': review.get('title', ''),
                'snippet': review.get('snippet', ''),
                'link': review.get('link', ''),
                'sentiment_score': pos_found - neg_found
            })
        
        total_analyzed = len(review_snippets)
        if total_analyzed > 0:
            sentiment_ratio = {
                'positive_percentage': round((positive_count / total_analyzed) * 100, 1),
                'negative_percentage': round((negative_count / total_analyzed) * 100, 1),
                'neutral_percentage': round(((total_analyzed - positive_count - negative_count) / total_analyzed) * 100, 1)
            }
        else:
            sentiment_ratio = {'error': 'Yorum analizi yapılamadı'}
        
        return {
            'total_reviews_analyzed': total_analyzed,
            'sentiment_analysis': sentiment_ratio,
            'sample_reviews': review_snippets[:5],
            'key_insights': self._extract_key_insights(review_snippets)
        }
    
    def _extract_key_insights(self, reviews: List[Dict]) -> List[str]:
        """
        Yorumlardan önemli içgörüler çıkarır
        """
        insights = []
        
        # Basit pattern matching
        common_patterns = {
            'quality': ['quality', 'durability', 'material', 'build'],
            'price': ['price', 'cost', 'value', 'expensive', 'cheap'],
            'shipping': ['shipping', 'delivery', 'packaging'],
            'functionality': ['function', 'feature', 'works', 'fit']
        }
        
        pattern_counts = {category: 0 for category in common_patterns}
        
        for review in reviews:
            text = (review.get('title', '') + ' ' + review.get('snippet', '')).lower()
            
            for category, keywords in common_patterns.items():
                if any(keyword in text for keyword in keywords):
                    pattern_counts[category] += 1
        
        # En çok bahsedilen konular
        sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
        
        for category, count in sorted_patterns[:3]:
            if count > 0:
                insights.append(f"Müşteriler en çok {category} konusunu bahsediyor ({count} kez)")
        
        return insights if insights else ['Yeterli veri bulunamadı']
    
    def _translate_keywords(self, keywords: List[str]) -> List[str]:
        """
        Türkçe kelimeleri İngilizce'ye çevirir
        """
        translation_map = {
            "tablet kılıfı": "tablet case",
            "akıllı kılıf": "smart case",
            "koruyucu kılıf": "protective case",
            "standlı kılıf": "stand case",
            "tablet": "tablet",
            "kilifi": "case",
            "akıllı": "smart",
            "koruyucu": "protective",
            "standlı": "stand"
        }
        
        english_keywords = []
        for keyword in keywords:
            # Tam eşleşme ara
            if keyword.lower() in translation_map:
                english_keywords.append(translation_map[keyword.lower()])
            else:
                # Kelime kelime çevir
                translated = keyword
                for tr, en in translation_map.items():
                    translated = translated.replace(tr, en)
                english_keywords.append(translated)
        
        return list(set(english_keywords))  # Tekrarları kaldır
    
    def _get_timestamp(self) -> str:
        """
        Zaman damgası oluşturur
        """
        from datetime import datetime
        return datetime.now().isoformat()

# Test fonksiyonu
def test_market_research():
    """
    Market Research Agent test
    """
    try:
        agent = MarketResearchAgent()
        
        # Vision testinden gelen anahtar kelimeler
        test_keywords = [
            "tablet kılıfı",
            "akıllı kılıf", 
            "koruyucu kılıf",
            "standlı kılıf"
        ]
        
        print("🧪 Market Research Agent Test Başlatılıyor...")
        print(f"🔑 Anahtar kelimeler: {test_keywords}")
        
        report = agent.analyze_competitor_data(test_keywords)
        
        print("\n📊 MARKET RESEARCH RAPORU:")
        print("=" * 50)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        
        return report
        
    except Exception as e:
        print(f"❌ Test hatası: {str(e)}")
        return None

if __name__ == "__main__":
    test_market_research()
