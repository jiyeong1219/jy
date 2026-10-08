"""Standalone HTML for the explicitly incomplete assumption-based screening run."""
import csv, html, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/assumption-screening'
r=json.loads((OUT/'results.json').read_text())
assert r['not_a_complete_cradle_to_gate_gwp'] and r['contribution_sum_check']
esc=lambda x:html.escape(str(x))
bom=list(csv.DictReader((ROOT/'data/bom.csv').open()))
labels={x['material_id']:x['material_name'] for x in bom}|{'plastic_conversion':'플라스틱 성형','metal_fabrication':'금속 가공','film_conversion':'포장 필름 변환','assembly':'조립'}
parts=sorted(r['contributions_kg_co2_eq'].items(),key=lambda x:-x[1]);total=r['three_gas_gwp100_subtotal_kg_co2_eq']
rows=''.join(f'<tr><td>{esc(labels[k])}</td><td>{v:.6f}</td><td>{v/total*100:.2f}%</td></tr>' for k,v in parts)
bars=''.join(f'<div class="bar"><span>{esc(labels[k])}</span><div class="track"><div style="width:{v/parts[0][1]*100:.2f}%"></div></div><b>{v:.3f}</b></div>' for k,v in parts)
assumption_ko=[
 '불명확한 나일론·POM·PC와 실리콘을 PP 수지로 대체했습니다. 특히 실리콘 대체는 화학적으로 적합한 공정이 아니며 결과 사용에 큰 제약이 있습니다.',
 '황동은 구리 공정으로 대체했습니다. 실제 황동 조성이나 합금 제조를 재현한 것은 아닙니다.',
 '전력은 실제 USLCI 역청탄 발전 공정으로 통일했습니다. 국가 평균 전력망이라는 주장은 하지 않습니다.',
 '플라스틱 구매량은 완제품 질량의 1.034배, 성형 전력은 1.79 kWh/kg으로 가정했습니다. 실제 USLCI PP 성형 자료를 다른 플라스틱에도 일반화한 가정입니다.',
 '금속 가공 0.5 kWh/kg, 필름 변환 0.5 kWh/kg, 조립 0.1 kWh/주전자는 분석자가 설정한 가정입니다.',
 '별도 공장 운송은 추가하지 않았습니다. 소비자 사용과 제품 폐기는 제외했습니다.',
 '미연결 배경 투입과 제조 폐기물 처리는 명시적으로 제외했습니다. 공정 참조 단위와 환산이 불가능한 투입도 제외 목록에 기록했습니다.',
 '기본흐름 중 공기로 배출되는 화석 CO₂·CH₄·N₂O만 특성화했습니다. 다른 온실가스는 0으로 판정한 것이 아니라 이 소계에서 빠져 있습니다.',
 'USLCI의 구체적 기원이 지정되지 않은 공기 배출 CO₂·CH₄는 화석 기원으로 가정했습니다. 자원 투입 흐름은 배출로 계산하지 않았습니다.',
 'TianGong 특성화 인자 원본을 사용했지만 IPCC 2021/2013 출처 표기가 혼재합니다. 검증된 공식 방법 버전 적용이라는 주장은 하지 않습니다.',
 '배포된 데이터의 기존 할당 상태를 그대로 사용했습니다. 시스템모델 일관성과 기존 누적부담의 중복 가능성은 별도 검토가 필요합니다.'
]
assumptions=''.join('<li>'+esc(x)+'</li>' for x in assumption_ko)
match_rows=''.join(f'<tr><td>{esc(x["material"])}</td><td>{x["mass_kg"]*1000:g}</td><td>{esc(x["provider"])}</td><td>{esc(x["proxy_rationale"])}</td><td>{x["purchase_multiplier"]:g}</td></tr>' for x in r['material_assumptions'])
gas_rows=''.join(f'<tr><td>{esc(gas)}</td><td>{mass:.9f}</td><td>{r["characterization_factors"][gas]:g}</td><td>{mass*r["characterization_factors"][gas]:.6f}</td></tr>' for gas,mass in r['gas_inventory_kg'].items())
energy_rows=''.join(f'<tr><td>{esc(labels.get(k,k))}</td><td>{v:.6f}</td></tr>' for k,v in r['foreground_energy_kwh'].items())
style='''body{font:16px/1.7 system-ui,"Malgun Gothic",sans-serif;background:#f0f5f7;color:#193644;margin:0}main{max-width:1100px;margin:32px auto;padding:0 20px}header{background:#123f50;color:white;padding:30px;border-radius:16px}h1{font-size:30px}section{background:white;padding:25px;border-radius:12px;margin:20px 0;border:1px solid #dce6eb}h2{font-size:23px;margin-top:0}.notice{background:#fff3dd;border-left:5px solid #d39b2d;padding:18px;margin-top:20px}.number{font-size:40px;font-weight:700;color:#126572}.muted{color:#526875}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:10px;text-align:left;border-bottom:1px solid #dce6eb;vertical-align:top}th{background:#edf4f6}code{font-size:13px;word-break:break-all}.bar{display:grid;grid-template-columns:210px 1fr 70px;gap:10px;margin:8px 0;font-size:14px}.track{background:#e9f0f3;align-self:center}.track div{height:16px;background:#197c85}a{color:#176b80}li{margin-bottom:8px}.formula{padding:16px;background:#edf4f6;font-size:23px}footer{font-size:13px;color:#526875;padding-bottom:30px}@media(max-width:650px){.bar{grid-template-columns:120px 1fr 55px;font-size:12px}h1{font-size:24px}section{padding:16px}}@media print{body{background:white}main{margin:0;padding:0}header{background:white;color:#193644;border:1px solid #ddd}section{break-inside:avoid}.scroll{overflow:visible}table{font-size:10px}}'''
report=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BC1 전기주전자 — 가정 기반 예비 LCA</title><style>{style}</style></head><body><main>
<header><p>2026-10-08 · ASSUMPTION-BASED SCREENING</p><h1>BC1 1 L 전기주전자<br>가정 기반 예비 환경영향평가</h1><p>선언단위: 제조·포장된 전기주전자 1개 · 제품 723 g + 포장 137.8 g</p></header>
<div class="notice"><strong>해석 필수:</strong> 아래 값은 불완전한 공급망과 대체 재료를 사용한 <strong>3종 온실가스 GWP100 소계</strong>입니다. 검증된 전체 공장 출하 LCA 총량, 제품 인증값 또는 특정 공식 IPCC 방법 버전의 확정 결과가 아닙니다.</div>
<section><h2>1. 계산 결과</h2><div class="number">{total:.3f} kg CO₂-eq</div><p>주전자 1개당 모델에 포함된 <strong>화석 CO₂ + 화석 CH₄ + N₂O</strong>의 가정 기반 GWP100 소계. 표시 반올림은 정확도를 뜻하지 않습니다.</p><p>계산값은 실제 DB 교환량과 특성화 인자로부터 산출했습니다. 부족한 재료·제조 조건에는 아래 가정을 적용했으며, 연결되지 않은 투입과 다른 온실가스는 별도로 기록했습니다. 이 값의 오차 방향·크기를 확인하지 못했으므로 보수적 추정 또는 상·하한이라고 부르지 않습니다.</p></section>
<section><h2>2. 재료·제조 기여도</h2><p>각 기여도는 동일한 A/B/C에서 그룹별 수요를 풀어 산출했으며 합계 검증을 통과했습니다. 대체 재료를 적용한 재료의 기여도는 실제 그 재료의 영향이 아닙니다.</p>{bars}<div class="scroll"><table><thead><tr><th>재료 / 단계</th><th>kg CO₂-eq 소계</th><th>모델 내 비중</th></tr></thead><tbody>{rows}</tbody></table></div><p class="muted">상위 3개 모델 기여 그룹: {', '.join(esc(labels[k]) for k,_ in parts[:3])}. 실제 제품의 지배적 영향 원인이라고 확정하지 않습니다.</p></section>
<section><h2>3. 인벤토리와 특성화</h2><table><thead><tr><th>공기 배출</th><th>kg/주전자</th><th>kg CO₂-eq/kg</th><th>환산 소계</th></tr></thead><tbody>{gas_rows}</tbody></table><p>특성화 인자 출처: TianGong 아카이브의 방법 UUID <code>{esc(r['method_uuid'])}</code>, 버전 <code>{esc(r['method_version'])}</code>. 원본의 서로 다른 출처연도 표기는 수정하지 않았으며 방법 버전 검증의 한계로 남겼습니다. 단순한 일반명/공기 구획 대응은 분석 가정이며 데이터베이스의 공식 기본흐름 crosswalk가 아닙니다.</p></section>
<section><h2>4. 행렬 계산과 검증</h2><div class="formula">A s = f → g = B s → h = C g</div><p>A는 기준 산출량으로 정규화한 공급자 연결, B는 포함한 3종 기본흐름의 공정별 배출량, C는 원본에서 읽은 GWP100 특성화 인자입니다. 역행렬 대신 SciPy <code>spsolve</code>를 사용했습니다. 선택 공정과 연결된 배경 공정은 {r['process_count']}개입니다.</p><p>최대 잔차 |As − f|: <code>{r['technosphere_residual_max']:.3e}</code>. 유한·비음수 활동량 확인 및 기여도 합계 확인 통과. 실제 BOM 12개·860.8 g 검증과 합성 알고리즘/BOM 테스트 15개가 별도로 통과했습니다. 수치 검증이 모델 가정의 과학적 타당성을 보장하지는 않습니다.</p></section>
<section><h2>5. 시스템 경계 및 가정</h2><p>원료, 모델링된 부품 변환·제조, 조립, 포장을 포함하려는 공장 출하 예비 모델입니다. 소비자 사용과 제품 폐기는 제외했습니다. 모든 필수 제조·배경 서비스가 포함됐다고 주장하지 않습니다.</p><ol>{assumptions}</ol><h3>가정한 전경 전력 투입</h3><table><thead><tr><th>단계</th><th>kWh/주전자</th></tr></thead><tbody>{energy_rows}</tbody></table></section>
<section><h2>6. BOM과 공급 공정 선택</h2><div class="scroll"><table><thead><tr><th>재료</th><th>완제품 질량 g</th><th>공급 공정 ID</th><th>대체 근거 / 제약</th><th>구매량 배수</th></tr></thead><tbody>{match_rows}</tbody></table></div><p><code>tg:copper</code>는 TianGong 구리 공정 UUID <code>{esc(r['tian_gong_copper_uuid'])}</code>입니다. 기존 입력만 기록된 구리 후보 대신, 실제 화석 CO₂ 배출과 산출량을 포함한 flash-smelting 공정을 선택했습니다. 나머지 ID는 USLCI 실제 공정 UUID이며 출처·버전·해시는 공정 manifest에 보존했습니다.</p></section>
<section><h2>7. 누락과 불확실성</h2><p>제외·미연결·LCI_RESULT 재연결 방지 기록 <strong>{r['cutoff_record_count']}건</strong>, 이 3종 특성화 범위 밖 기본흐름 기록 <strong>{r['uncharacterized_record_count']}건</strong>을 남겼습니다. 이는 고유 흐름 개수나 모두 온실가스라는 뜻이 아닙니다. 공급망과 GWP100 특성화 범위는 불완전합니다.</p><p>할당·누적부담 중복·지역 및 연도 불일치, 실리콘/나일론 등의 부적합한 대체가 큰 모델 불확실성을 만듭니다. 확률분포·몬테카를로·P05/P95는 계산하지 않았습니다. {total:.3f}라는 표시 정밀도를 실측 정확도로 해석하지 마세요.</p></section>
<section><h2>8. 원본 출처와 재현</h2><p>실제 인벤토리: USLCI 1.2025-06.0 JSON-LD, TianGong 역사적 ILCD. <a href="https://github.com/FLCAC-admin/uslci-content/blob/dev/docs/release_info/release-downloads.md">USLCI 공식 배포 안내</a> · <a href="https://github.com/tiangong-lca/data">TianGong data</a>.</p><p>GitHub 프로젝트: <a href="https://github.com/jiyeong1219/jy">jiyeong1219/jy</a>. Python 의존성을 설치하고 공개 원본을 준비한 다음 <code>python scripts/screening_lca.py</code>, <code>python scripts/build_screening_report.py</code>를 실행합니다. 다운로드 절차는 README와 DATABASE_ACCESS 문서에 있습니다.</p><p><code>results/assumption-screening/</code>에 A/B 행렬, C/f/s/g/h 벡터, 기여도 CSV, 공급자 연결, 제외 항목, 흐름 대응과 특성화 근거를 저장했습니다. 원본 인벤토리는 해시로 검증합니다. 이 HTML은 외부 스타일·스크립트 없이 열립니다.</p><p>이 결과는 사용자가 대체·제조 가정을 허용한 후 작성한 별도 시나리오입니다. 이전 미계산 기준 상태와 검증 기록은 덮어쓰지 않았습니다. 이전 수치가 없어 수정 전후 백분율 차이는 해당 없음입니다. Codex가 공정 선택·모델·코드를 작성했으며 독립적 사람의 최종 검증은 기록되지 않았습니다.</p></section><footer>결과 상태: 가정 기반, 불완전한 3종 온실가스 소계. 실제 전체 LCA 완성 또는 인증을 뜻하지 않습니다.</footer></main></body></html>'''
path=ROOT/'results/report.html';path.write_text(report,encoding='utf-8')
assert report.count('<html')==1 and report.count('</html>')==1 and '불완전' in report
print('Created standalone HTML:',path)
