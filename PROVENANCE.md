# Provenance

This dataset describes real Massachusetts towns, but each column comes from a
different source, and the columns reflect different years and methodologies.
It is stitched together for a teaching demo.

**Do not use this data for any real decision** (buying a home, choosing a school
district, judging a town's safety). It is here to demonstrate MCP architecture,
and to practice the habit of recording where every number came from.

Retrieved: 2026-07-22.

## By column

| column | source | unit | vintage | method / caveats |
| --- | --- | --- | --- | --- |
| `median_home_price` | Zillow Home Value Index (ZHVI), town level | USD | ~2026 (monthly) | Typical whole-town home value. Some Zillow pages returned HTTP 403; those values came from Zillow's search-indexed snippet. ZIP-level and neighborhood-level figures were deliberately not used. |
| `violent_crime_rate` | NeighborhoodScout | incidents per 1,000 | 2024 (FBI-derived, released Oct 2025) | Values already per 1,000 where reported; a few converted from per-100,000. Wakefield lacks direct FBI reporting, so its figure is NeighborhoodScout-modeled. |
| `school_rating` | GreatSchools | 1-10 | ~2025-2026 | GreatSchools publishes no single district number, so this is the rounded average of the town's rated public schools. Several towns are borderline (e.g. Malden, Somerville ~5.5). Newton uses only its two high schools (both 10) and therefore overstates the district. |
| `distance_to_boston_mi` | computed | miles | n/a | Haversine great-circle distance from the town's Census/Wikipedia centroid to Boston City Hall (42.3601, -71.0589). Straight line, not travel time. |
| `population` | US Census / ACS | count | 2020 decennial or later ACS estimate | Vintage varies by town; see per-town notes. |

## By town

### Winchester

- median_home_price = 1,433,087: [Zillow ZHVI](https://www.zillow.com/home-values/41741/winchester-ma/)
- violent_crime_rate = 0.17 per 1,000, vintage 2024: [NeighborhoodScout](https://www.neighborhoodscout.com/ma/winchester/crime)
- school_rating = 8 (avg of town public schools ~8): [GreatSchools](https://www.greatschools.org/massachusetts/winchester/winchester-school-district/)
- distance_to_boston_mi = 7.5: computed from centroid (42.45222, -71.1375) [source](https://en.wikipedia.org/wiki/Winchester,_Massachusetts)
- population = 22,970, vintage 2020 Census: [source](https://en.wikipedia.org/wiki/Winchester,_Massachusetts)

### Lexington

- median_home_price = 1,626,916: [Zillow ZHVI](https://www.zillow.com/home-values/19005/lexington-ma/)
- violent_crime_rate = 0.52 per 1,000, vintage 2024: [NeighborhoodScout](https://www.neighborhoodscout.com/ma/lexington/crime)
- school_rating = 9 (avg of town public schools ~9): [GreatSchools](https://www.greatschools.org/massachusetts/lexington/)
- distance_to_boston_mi = 10.5: computed from centroid (42.4475, -71.2275) [source](https://en.wikipedia.org/wiki/Lexington,_Massachusetts)
- population = 34,295, vintage ACS 2024 5-yr: [source](https://censusreporter.org/profiles/16000US2535250-lexington-ma/)

### Arlington

- median_home_price = 995,240: [Zillow ZHVI](https://www.zillow.com/home-values/43936/arlington-ma/)
- violent_crime_rate = 0.55 per 1,000, vintage 2024: [NeighborhoodScout](https://www.neighborhoodscout.com/ma/arlington/crime)
- school_rating = 7 (avg of town public schools ~6.5 (2023 profile)): [GreatSchools](https://www.greatschools.org/massachusetts/arlington/)
- distance_to_boston_mi = 6.3: computed from centroid (42.41528, -71.15694) [source](https://en.wikipedia.org/wiki/Arlington,_Massachusetts)
- population = 46,308, vintage 2020 Census: [source](https://en.wikipedia.org/wiki/Arlington,_Massachusetts)

### Belmont

- median_home_price = 1,349,551: [Zillow ZHVI](https://www.zillow.com/home-values/10344/belmont-ma/)
- violent_crime_rate = 0.51 per 1,000, vintage 2024: [NeighborhoodScout](https://www.neighborhoodscout.com/ma/belmont/crime)
- school_rating = 9 (avg of town's 6 public schools ~8.83): [GreatSchools](https://www.greatschools.org/massachusetts/belmont/)
- distance_to_boston_mi = 6.6: computed from centroid (42.39583, -71.17917) [source](https://en.wikipedia.org/wiki/Belmont,_Massachusetts)
- population = 27,175, vintage ACS 2024 5-yr: [source](http://censusreporter.org/profiles/06000US2501705070-belmont-town-middlesex-county-ma/)

### Newton

- median_home_price = 1,395,369: [Zillow ZHVI](https://www.zillow.com/home-values/40013/newton-ma/)
- violent_crime_rate = 0.5 per 1,000, vintage 2024: [NeighborhoodScout](https://www.neighborhoodscout.com/ma/newton/crime)
- school_rating = 10 (avg of Newton North+South HS (both 10); overstates district): [GreatSchools](https://www.greatschools.org/massachusetts/newton/)
- distance_to_boston_mi = 7.9: computed from centroid (42.33694, -71.20972) [source](https://en.wikipedia.org/wiki/Newton,_Massachusetts)
- population = 88,415, vintage Census V2023 est: [source](https://www.census.gov/quickfacts/fact/table/newtoncitymassachusetts/PST045224)

### Woburn

- median_home_price = 653,416: [Zillow ZHVI](https://www.zillow.com/home-values/58489/woburn-ma-01801/)
- violent_crime_rate = 2.1 per 1,000, vintage 2024: [NeighborhoodScout](https://www.neighborhoodscout.com/ma/woburn/crime)
- school_rating = 4 (avg of 7 public schools ~4.43): [GreatSchools](https://www.greatschools.org/massachusetts/woburn/)
- distance_to_boston_mi = 9.5: computed from centroid (42.47917, -71.15278) [source](https://en.wikipedia.org/wiki/Woburn,_Massachusetts)
- population = 40,876, vintage 2020 Census: [source](https://en.wikipedia.org/wiki/Woburn,_Massachusetts)

### Medford

- median_home_price = 855,081: [Zillow ZHVI](https://www.zillow.com/home-values/53250/medford-ma/)
- violent_crime_rate = 1.82 per 1,000, vintage 2024: [NeighborhoodScout](https://www.neighborhoodscout.com/ma/medford/crime)
- school_rating = 5 (avg of 7 public schools ~4.6): [GreatSchools](https://www.greatschools.org/massachusetts/medford/)
- distance_to_boston_mi = 4.7: computed from centroid (42.4184, -71.1062) [source](https://en.wikipedia.org/wiki/Medford,_Massachusetts)
- population = 59,659, vintage 2020 Census: [source](https://en.wikipedia.org/wiki/Medford,_Massachusetts)

### Burlington

- median_home_price = 804,017: [Zillow ZHVI](https://www.zillow.com/home-values/37661/burlington-ma/)
- violent_crime_rate = 2.26 per 1,000, vintage 2024: [NeighborhoodScout](https://www.neighborhoodscout.com/ma/burlington/crime)
- school_rating = 6 (avg of 6 public schools ~6.0): [GreatSchools](https://www.greatschools.org/massachusetts/burlington/)
- distance_to_boston_mi = 12.2: computed from centroid (42.50472, -71.19611) [source](https://en.wikipedia.org/wiki/Burlington,_Massachusetts)
- population = 26,377, vintage 2020 Census: [source](https://en.wikipedia.org/wiki/Burlington,_Massachusetts)

### Reading

- median_home_price = 801,568: [Zillow ZHVI](https://www.zillow.com/home-values/6695/reading-ma/)
- violent_crime_rate = 0.38 per 1,000, vintage 2024: [NeighborhoodScout](https://www.neighborhoodscout.com/ma/reading/crime)
- school_rating = 8 (avg of 8 public schools ~8.0): [GreatSchools](https://www.greatschools.org/massachusetts/reading/)
- distance_to_boston_mi = 11.6: computed from centroid (42.52556, -71.09583) [source](https://en.wikipedia.org/wiki/Reading,_Massachusetts)
- population = 25,518, vintage 2020 Census: [source](https://en.wikipedia.org/wiki/Reading,_Massachusetts)

### Melrose

- median_home_price = 843,099: [Zillow ZHVI](https://www.zillow.com/home-values/23017/melrose-ma/)
- violent_crime_rate = 1.0 per 1,000, vintage 2024: [NeighborhoodScout](https://www.neighborhoodscout.com/ma/melrose/crime)
- school_rating = 8 (avg of 7 public schools ~7.86): [GreatSchools](https://www.greatschools.org/massachusetts/melrose/melrose-school-district/)
- distance_to_boston_mi = 6.8: computed from centroid (42.4583, -71.0667) [source](https://en.wikipedia.org/wiki/Melrose,_Massachusetts)
- population = 29,817, vintage 2020 Census: [source](https://en.wikipedia.org/wiki/Melrose,_Massachusetts)

### Stoneham

- median_home_price = 676,728: [Zillow ZHVI](https://www.zillow.com/stoneham-ma/home-values/)
- violent_crime_rate = 1.43 per 1,000, vintage 2024: [NeighborhoodScout](https://www.neighborhoodscout.com/ma/stoneham/crime)
- school_rating = 7 (avg of 5 public schools ~6.6): [GreatSchools](https://www.greatschools.org/massachusetts/stoneham/)
- distance_to_boston_mi = 8.5: computed from centroid (42.48, -71.1) [source](https://en.wikipedia.org/wiki/Stoneham,_Massachusetts)
- population = 23,244, vintage 2020 Census: [source](https://en.wikipedia.org/wiki/Stoneham,_Massachusetts)

### Wakefield

- median_home_price = 743,417: [Zillow ZHVI](https://www.zillow.com/home-values/7739/wakefield-ma/)
- violent_crime_rate = 1.71 per 1,000, vintage 2024 (modeled; no direct FBI reporting): [NeighborhoodScout](https://www.neighborhoodscout.com/ma/wakefield/crime)
- school_rating = 7 (avg of rated public schools ~7.2): [GreatSchools](https://www.greatschools.org/massachusetts/wakefield/)
- distance_to_boston_mi = 10.1: computed from centroid (42.50639, -71.07333) [source](https://en.wikipedia.org/wiki/Wakefield,_Massachusetts)
- population = 27,090, vintage 2020 Census: [source](https://en.wikipedia.org/wiki/Wakefield,_Massachusetts)

### Malden

- median_home_price = 613,378: [Zillow ZHVI](https://www.zillow.com/home-values/28939/malden-ma/)
- violent_crime_rate = 2.91 per 1,000, vintage 2024: [NeighborhoodScout](https://www.neighborhoodscout.com/ma/malden/crime)
- school_rating = 6 (avg of 6 public schools ~5.5 (borderline)): [GreatSchools](https://www.greatschools.org/massachusetts/malden/)
- distance_to_boston_mi = 4.5: computed from centroid (42.425, -71.06667) [source](https://en.wikipedia.org/wiki/Malden,_Massachusetts)
- population = 66,263, vintage 2020 Census: [source](https://en.wikipedia.org/wiki/Malden,_Massachusetts)

### Somerville

- median_home_price = 885,311: [Zillow ZHVI](https://www.zillow.com/home-values/54458/somerville-ma/)
- violent_crime_rate = 2.22 per 1,000, vintage 2024: [NeighborhoodScout](https://www.neighborhoodscout.com/ma/somerville/crime)
- school_rating = 6 (avg of 8 public schools ~5.5 (borderline)): [GreatSchools](https://www.greatschools.org/massachusetts/somerville/)
- distance_to_boston_mi = 2.8: computed from centroid (42.3875, -71.1) [source](https://en.wikipedia.org/wiki/Somerville,_Massachusetts)
- population = 81,045, vintage 2020 Census: [source](https://en.wikipedia.org/wiki/Somerville,_Massachusetts)

### Hopkinton

- median_home_price = 877,055: [Zillow ZHVI](https://www.zillow.com/home-values/398002/hopkinton-ma/)
- violent_crime_rate = 1.0 per 1,000, vintage 2024: [NeighborhoodScout](https://www.neighborhoodscout.com/ma/hopkinton/crime)
- school_rating = 9 (HS 10/10 confirmed; other schools above-average, district est. ~9): [GreatSchools](https://www.greatschools.org/massachusetts/hopkinton/)
- distance_to_boston_mi = 25.4: computed from centroid (42.22861, -71.52306) [source](https://en.wikipedia.org/wiki/Hopkinton,_Massachusetts)
- population = 18,758, vintage 2020 Census: [source](https://en.wikipedia.org/wiki/Hopkinton,_Massachusetts)
