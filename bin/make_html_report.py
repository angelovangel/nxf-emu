#!/usr/bin/env python3
import sys
import os
import json
import csv

def parse_rel_abundance(file_path):
    data = []
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                if row.get('tax_id') in ['unmapped', 'mapped_filtered', 'mapped_unclassified']:
                    continue
                abundance = float(row.get('abundance', 0))
                if abundance > 0:
                    data.append({
                        'species': row.get('species', 'Unknown'),
                        'genus': row.get('genus', 'Unknown'),
                        'family': row.get('family', 'Unknown'),
                        'class': row.get('class', 'Unknown'),
                        'phylum': row.get('phylum', 'Unknown'),
                        'superkingdom': row.get('superkingdom', 'Unknown'),
                        'abundance': abundance,
                        'counts': float(row.get('estimated counts', 0))
                    })
    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)
    return data

def parse_combined_abundance(file_path):
    data = {"samples": [], "taxa": []}
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            # Extract sample names (columns after the taxonomic ranks)
            tax_cols = ['species', 'genus', 'family', 'order', 'class', 'phylum', 'superkingdom']
            data["samples"] = [col for col in reader.fieldnames if col not in tax_cols]
            
            for row in reader:
                # Convert abundances to float, handle empty/missing as 0
                abundances = []
                for s in data["samples"]:
                    try:
                        val = float(row.get(s, 0) or 0)
                        abundances.append(val)
                    except ValueError:
                        abundances.append(0.0)
                
                if any(a > 0 for a in abundances):
                    taxon_entry = {col: row.get(col, 'Unknown') for col in tax_cols}
                    taxon_entry["abundances"] = abundances
                    data["taxa"].append(taxon_entry)
    except Exception as e:
        print(f"Warning: Could not parse combined results {file_path}: {e}", file=sys.stderr)
    return data

def main():
    if len(sys.argv) < 3:
        print("Usage: make_html_report.py <summary_tsv> <combined_tsv> [rel_abundance_files...]")
        sys.exit(1)

    summary_tsv = sys.argv[1]
    combined_tsv = sys.argv[2]
    rel_abundance_files = sys.argv[3:]

    # Parse summary counts
    summary_data = []
    headers = []
    try:
        with open(summary_tsv, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
            headers = reader.fieldnames
            for row in reader:
                summary_data.append(row)
    except Exception as e:
        print(f"Error: Could not parse {summary_tsv}: {e}", file=sys.stderr)

    # Parse combined results for heatmap
    heatmap_data = parse_combined_abundance(combined_tsv)

    # Parse all rel-abundance files for bar plots
    all_samples = []
    for fpath in rel_abundance_files:
        sample_name = os.path.basename(fpath).replace('_rel-abundance.tsv', '').replace('.fastq_rel-abundance.tsv', '')
        data = parse_rel_abundance(fpath)
        if data:
            all_samples.append({'name': sample_name, 'data': data})

    table_header_html = "".join([f'<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>' for h in headers]) if headers else ""
    
    table_rows_html = ""
    for row in summary_data:
        table_rows_html += "<tr>"
        
        # Get basis for percentage (filtered_reads or raw_reads)
        total_reads = float(row.get('filtered_reads', row.get('raw_reads', 0)) or 1)
        if total_reads == 0: total_reads = 1
        
        for h in headers:
            val = row.get(h, "")
            display_val = val
            
            # Format columns that are counts but not the basis columns
            if h in ['mapped', 'unmapped', 'mapped_filtered', 'mapped_unclassified']:
                try:
                    count_val = float(val)
                    perc = (count_val / total_reads) * 100
                    display_val = f"{int(count_val)} ({perc:.1f}%)"
                except:
                    pass
            elif h in ['raw_reads', 'filtered_reads']:
                try:
                    display_val = f"{int(float(val))}"
                except:
                    pass
            
            table_rows_html += f'<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{display_val}</td>'
        table_rows_html += "</tr>"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Emu Abundance Report</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
        .heatmap-cell {{ transition: all 0.2s; }}
        .heatmap-cell:hover {{ transform: scale(1.1); z-index: 10; }}
    </style>
</head>
<body class="bg-gray-100 min-h-screen p-6">
    <div class="max-w-7xl mx-auto space-y-8">
        <!-- Pipeline Summary -->
        <div class="bg-white shadow-xl rounded-2xl p-8">
            <h1 class="text-xl font-bold text-gray-900 mb-6 border-b pb-4">Pipeline Summary</h1>
            <div class="overflow-x-auto border rounded-xl">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>{table_header_html}</tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">{table_rows_html}</tbody>
                </table>
            </div>
        </div>

        <!-- Global Controls -->
        <div class="bg-white shadow-xl rounded-2xl p-8">
            <h1 class="text-xl font-bold text-gray-900 mb-6 border-b pb-4">Report Controls</h1>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 bg-gray-50 p-4 rounded-xl">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Group By</label>
                    <select id="rankSelect" class="w-full border-gray-300 rounded-md shadow-sm p-2 outline-none focus:ring-2 focus:ring-indigo-500">
                        <option value="superkingdom">Superkingdom</option>
                        <option value="phylum">Phylum</option>
                        <option value="class">Class</option>
                        <option value="family">Family</option>
                        <option value="genus" selected>Genus</option>
                        <option value="species">Species</option>
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Top N Taxa</label>
                    <input type="number" id="topNInput" value="10" min="1" max="100" class="w-full border-gray-300 rounded-md shadow-sm p-2 outline-none focus:ring-2 focus:ring-indigo-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Select Samples</label>
                    <div class="relative">
                        <button id="dropdownButton" class="w-full flex justify-between items-center border border-gray-300 rounded-md shadow-sm p-2 bg-white text-sm outline-none focus:ring-2 focus:ring-indigo-500">
                            <span id="dropdownLabel">All Samples Selected</span>
                            <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        </button>
                        <div id="sampleDropdown" class="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg hidden max-h-64 overflow-y-auto">
                            <div class="p-2 border-b border-gray-100 flex justify-between">
                                <button onclick="toggleAllSamples(true)" class="text-xs text-indigo-600 hover:text-indigo-800 font-semibold">Select All</button>
                                <button onclick="toggleAllSamples(false)" class="text-xs text-indigo-600 hover:text-indigo-800 font-semibold">Clear</button>
                            </div>
                            <div id="sampleSelector" class="p-1"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Abundance Plots -->
        <div class="bg-white shadow-xl rounded-2xl p-8">
            <h1 class="text-xl font-bold text-gray-900 mb-6 border-b pb-4">Taxonomic Distribution</h1>
            <div id="chartContainer" class="relative min-h-[300px]">
                <div id="chart-tooltip" class="absolute pointer-events-none z-50 p-3 bg-gray-800 text-white rounded shadow-xl opacity-0 transition-opacity duration-200 w-72 overflow-hidden"></div>
                <canvas id="chartCanvas"></canvas>
            </div>
        </div>

        <!-- Heatmap Section -->
        <div class="bg-white shadow-xl rounded-2xl p-8">
            <h1 class="text-xl font-bold text-gray-900 mb-6 border-b pb-4">Abundance Heatmap</h1>
            <div class="overflow-x-auto border rounded-xl bg-gray-50">
                <div id="heatmapContainer" class="p-4 inline-block min-w-full">
                    <!-- Heatmap will be generated here -->
                </div>
            </div>
        </div>
    </div>

    <script>
        const samples = {json.dumps(all_samples)};
        const heatmapData = {json.dumps(heatmap_data)};
        let chartInstance = null;

        // --- Dropdown Management ---
        document.getElementById('dropdownButton').addEventListener('click', () => {{
            document.getElementById('sampleDropdown').classList.toggle('hidden');
        }});

        document.addEventListener('click', (e) => {{
            const dropdown = document.getElementById('sampleDropdown');
            const button = document.getElementById('dropdownButton');
            if (!dropdown.contains(e.target) && !button.contains(e.target)) {{
                dropdown.classList.add('hidden');
            }}
        }});

        function toggleAllSamples(checked) {{
            document.querySelectorAll('#sampleSelector input').forEach(cb => cb.checked = checked);
            updateChart();
            renderHeatmap();
        }}

        function populateSampleSelector() {{
            const container = document.getElementById('sampleSelector');
            samples.forEach((s, i) => {{
                const div = document.createElement('div');
                div.className = 'flex items-center px-2 py-1 hover:bg-gray-100 rounded cursor-pointer';
                div.onclick = (e) => {{
                    if (e.target.tagName !== 'INPUT') {{
                        const cb = div.querySelector('input');
                        cb.checked = !cb.checked;
                        updateChart();
                        renderHeatmap();
                    }}
                }};
                div.innerHTML = `<input type="checkbox" id="sample-${{i}}" value="${{s.name}}" checked class="mr-2 cursor-pointer">
                                 <label for="sample-${{i}}" class="text-sm truncate w-full cursor-pointer">${{s.name}}</label>`;
                div.querySelector('input').addEventListener('change', (e) => {{
                    e.stopPropagation();
                    updateChart();
                    renderHeatmap();
                }});
                container.appendChild(div);
            }});
        }}

        function getSelectedSampleNames() {{
            return Array.from(document.querySelectorAll('#sampleSelector input:checked')).map(cb => cb.value);
        }}

        // --- Heatmap Logic ---
        function getHeatmapColor(val) {{
            if (val <= 0) return {{ bg: '#f9fafb', text: 'black' }};
            const scaled = Math.pow(val, 0.4);
            const hue = 240;
            const saturation = 70;
            const lightness = 100 - (scaled * 60);
            return {{
                bg: `hsl(${{hue}}, ${{saturation}}%, ${{lightness}}%)`,
                text: lightness < 60 ? 'white' : 'black'
            }};
        }}

        function renderHeatmap() {{
            const rank = document.getElementById('rankSelect').value;
            const topN = parseInt(document.getElementById('topNInput').value) || 10;
            const container = document.getElementById('heatmapContainer');
            const selectedNames = getSelectedSampleNames();
            
            if (selectedNames.length === 0) {{
                container.innerHTML = '<p class="text-gray-500 italic p-4">No samples selected</p>';
                return;
            }}

            const sampleIndices = selectedNames.map(name => heatmapData.samples.indexOf(name));
            
            // Aggregate by selected rank
            const aggregated = {{}};
            heatmapData.taxa.forEach(t => {{
                const taxonName = t[rank] || 'Unknown';
                if (!aggregated[taxonName]) {{
                    aggregated[taxonName] = new Array(heatmapData.samples.length).fill(0);
                }}
                t.abundances.forEach((val, i) => {{
                    aggregated[taxonName][i] += val;
                }});
            }});

            const allTaxa = Object.keys(aggregated).map(name => ({{
                name: name,
                sum: sampleIndices.reduce((acc, idx) => acc + (aggregated[name][idx] || 0), 0),
                abundances: aggregated[name]
            }}))
            .filter(t => t.sum > 0)
            .sort((a, b) => b.sum - a.sum);

            const sortedTaxa = allTaxa.slice(0, topN);
            
            // Calculate "Other" row
            if (allTaxa.length > topN) {{
                const otherAbundances = new Array(heatmapData.samples.length).fill(0);
                allTaxa.slice(topN).forEach(t => {{
                    t.abundances.forEach((val, i) => {{
                        otherAbundances[i] += val;
                    }});
                }});
                sortedTaxa.push({{
                    name: 'Other',
                    sum: otherAbundances.reduce((acc, val) => acc + val, 0),
                    abundances: otherAbundances
                }});
            }}

            let html = '<table class="border-collapse text-xs">';
            // Header
            html += '<thead><tr><th class="p-2 text-left bg-white border sticky left-0 z-20">Taxon</th>';
            selectedNames.forEach(name => {{
                html += `<th class="p-2 text-center bg-gray-100 border whitespace-nowrap truncate max-w-[150px]">${{name}}</th>`;
            }});
            html += '</tr></thead><tbody>';

            // Rows
            sortedTaxa.forEach(t => {{
                const isOther = t.name === 'Other';
                html += `<tr><td class="p-2 font-medium ${{isOther ? 'bg-gray-50 italic' : 'bg-white'}} border sticky left-0 z-10 whitespace-nowrap shadow-sm">${{t.name}}</td>`;
                sampleIndices.forEach(idx => {{
                    const val = t.abundances[idx] || 0;
                    const {{bg, text}} = getHeatmapColor(val);
                    html += `<td class="p-2 text-center border heatmap-cell" style="background-color: ${{bg}}; color: ${{text}}" title="${{t.name}} in ${{heatmapData.samples[idx]}}: ${{(val * 100).toFixed(4)}}%">
                                ${{val > 0.001 ? (val * 100).toFixed(1) + '%' : (val > 0 ? '<0.1%' : '-')}}
                             </td>`;
                }});
                html += '</tr>';
            }});
            html += '</tbody></table>';
            container.innerHTML = html;
        }}

        // --- Chart Logic ---
        function getColor(name, index) {{
            if (name.startsWith('Other')) return '#9ca3af';
            const colors = ['#4f46e5', '#ef4444', '#10b981', '#f59e0b', '#3b82f6', '#8b5cf6', '#ec4899', '#6366f1', '#14b8a6', '#f97316'];
            return colors[index % colors.length];
        }}

        function externalTooltipHandler(context) {{
            const tooltipEl = document.getElementById('chart-tooltip');
            const {{chart, tooltip}} = context;
            if (tooltip.opacity === 0) {{ tooltipEl.style.opacity = 0; return; }}

            if (tooltip.body) {{
                const datasetIndex = tooltip.dataPoints[0].datasetIndex;
                const dataset = chart.data.datasets[datasetIndex];
                const labels = chart.data.labels;
                let html = `<div class="font-bold border-b border-gray-600 mb-2 pb-1 text-sm mr-2" style="color: ${{dataset.backgroundColor}}">${{dataset.label}}</div><ul class="text-xs space-y-1">`;
                for (let i = 0; i < labels.length; i++) {{
                    const isHovered = i === tooltip.dataPoints[0].dataIndex ? 'bg-gray-700 rounded' : '';
                    html += `<li class="flex justify-between items-center p-1 ${{isHovered}}"><span class="truncate mr-4">${{labels[i]}}</span><span class="font-mono">${{dataset.data[i].toFixed(2)}}%</span></li>`;
                }}
                tooltipEl.innerHTML = html + '</ul>';
            }}
            tooltipEl.style.opacity = 1;
            tooltipEl.style.left = chart.canvas.offsetLeft + 10 + 'px';
            tooltipEl.style.top = Math.min(chart.canvas.offsetTop + 10, chart.height - tooltipEl.offsetHeight - 10) + 'px';
        }}

        function updateChart() {{
            const rank = document.getElementById('rankSelect').value;
            const topN = parseInt(document.getElementById('topNInput').value) || 10;
            const selectedNames = getSelectedSampleNames();
            const selectedSamples = samples.filter(s => selectedNames.includes(s.name));
            
            document.getElementById('dropdownLabel').innerText = selectedNames.length === samples.length ? 'All Samples Selected' : (selectedNames.length === 0 ? 'No Samples Selected' : `${{selectedNames.length}} Samples Selected`);

            const container = document.getElementById('chartContainer');
            if (selectedSamples.length === 0) {{
                if (chartInstance) chartInstance.destroy();
                chartInstance = null;
                container.style.height = '300px';
                return;
            }}

            container.style.height = Math.max(300, selectedSamples.length * 40 + 100) + 'px';

            const globalTotals = {{}};
            const presence = {{}};
            selectedSamples.forEach(s => {{
                s.data.forEach(d => {{
                    const taxon = d[rank] || 'Unknown';
                    globalTotals[taxon] = (globalTotals[taxon] || 0) + d.abundance;
                    if (!presence[taxon]) presence[taxon] = new Set();
                    if (d.abundance > 0) presence[taxon].add(s.name);
                }});
            }});

            const commonTaxa = Object.keys(globalTotals).filter(t => presence[t].size === selectedSamples.length);
            const topTaxa = commonTaxa.sort((a, b) => globalTotals[b] - globalTotals[a]).slice(0, topN);

            const datasets = topTaxa.map((taxon, i) => {{
                const taxonData = selectedSamples.map(s => {{
                    const match = s.data.filter(d => d[rank] === taxon);
                    return {{ abundance: match.reduce((sum, d) => sum + d.abundance, 0) * 100, counts: Math.round(match.reduce((sum, d) => sum + d.counts, 0)) }};
                }});
                return {{ label: taxon, data: taxonData.map(d => d.abundance), counts: taxonData.map(d => d.counts), backgroundColor: getColor(taxon, i) }};
            }});

            const otherData = selectedSamples.map(s => {{
                const other = s.data.filter(d => !topTaxa.includes(d[rank]));
                return {{ abundance: other.reduce((sum, d) => sum + d.abundance, 0) * 100, counts: Math.round(other.reduce((sum, d) => sum + d.counts, 0)) }};
            }});
            
            if (otherData.some(v => v.abundance > 0)) {{
                datasets.push({{ label: 'Other', data: otherData.map(d => d.abundance), counts: otherData.map(d => d.counts), backgroundColor: '#9ca3af' }});
            }}

            if (chartInstance) chartInstance.destroy();
            chartInstance = new Chart(document.getElementById('chartCanvas'), {{
                type: 'bar',
                data: {{ labels: selectedSamples.map(s => s.name), datasets }},
                options: {{
                    indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                    barPercentage: 0.8, categoryPercentage: 1.0,
                    scales: {{ x: {{ stacked: true, max: 100, title: {{ display: true, text: 'Relative Abundance (%)' }} }}, y: {{ stacked: true }} }},
                    plugins: {{ legend: {{ position: 'right' }}, tooltip: {{ enabled: false, external: externalTooltipHandler }} }}
                }}
            }});
        }}

        document.getElementById('rankSelect').addEventListener('change', () => {{
            updateChart();
            renderHeatmap();
        }});
        document.getElementById('topNInput').addEventListener('change', () => {{
            updateChart();
            renderHeatmap();
        }});
        
        populateSampleSelector();
        updateChart();
        renderHeatmap();
    </script>
</body>
</html>
"""
    with open('nxf-emu-report.html', 'w') as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
