function drawCircles(data) {
  const width = 800;
  const height = 600;

  d3.select("#chart").selectAll("*").remove();

  const svg = d3.select("#chart").append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("preserveAspectRatio", "xMidYMid meet")
    .style("width", "100%")
    .style("height", "auto");

  const files = Object.entries(data).filter(([filename, _]) => !filename.toLowerCase().includes("license"));

  const nodes = {
    name: "root",
    children: files.map(([filename, info]) => ({
      name: filename,
      // Escalado con log + corrección por valores pequeños
      value: Math.min(Math.log((info.size_kb || 0.1) + 1), 6),
      info: info
    }))
  };

  const root = d3.hierarchy(nodes).sum(d => d.value);

  const pack = d3.pack()
    .size([width, height])
    .padding(5);

  const packedRoot = pack(root);

  const node = svg.selectAll("g")
    .data(packedRoot.leaves())
    .enter()
    .append("g")
    .attr("transform", d => `translate(${d.x},${d.y})`)
    .style("cursor", "pointer");

  const tooltip = d3.select("#tooltip");

  node.append("circle")
    .attr("r", d => d.r)
    .attr("fill", (_, i) => d3.schemeCategory10[i % 10])
    .on("mouseover", (event, d) => {
      tooltip
        .style("opacity", 1)
        .html(`
          <strong>${d.data.name}</strong><br/>
          Codificación: ${d.data.info.encoding || "N/A"}<br/>
          Granularidad: ${d.data.info.granularity || "N/A"}<br/>
          Filas: ${d.data.info.num_rows || "N/A"}<br/>
          Tamaño (KB): ${d.data.info.size_kb || "N/A"}
        `)
        .style("left", (event.pageX + 15) + "px")
        .style("top", (event.pageY - 28) + "px");
    })
    .on("mousemove", (event) => {
      tooltip
        .style("left", (event.pageX + 15) + "px")
        .style("top", (event.pageY - 28) + "px");
    })
    .on("mouseout", () => {
      tooltip.style("opacity", 0);
    })
    .on("click", (event, d) => {
      const archivo = d.data.name;
      window.location.href = `/info?archivo=${encodeURIComponent(archivo)}`;
    });

  node.append("text")
    .attr("text-anchor", "middle")
    .attr("dy", ".35em")
    .text(d => d.data.name.replace('.txt', ''))
    .style("pointer-events", "none")
    .style("font-size", d => Math.min(12, d.r / 2.5) + "px");
}

function drawTimelineChart(data) {
  const chartDiv = d3.select("#chart");
  const tooltip = d3.select("#tooltip");

  chartDiv.selectAll("*").remove();

  const width = 800;
  const height = 300;
  const margin = {top: 40, right: 40, bottom: 80, left: 60};

  const svg = chartDiv.append("svg")
    .attr("width", width)
    .attr("height", height);

  const files = Object.entries(data).filter(([filename, _]) => !filename.toLowerCase().includes("license"));

  const xScale = d3.scaleBand()
    .domain(files.map(d => d[0]))
    .range([margin.left, width - margin.right])
    .padding(0.2);

  const values = files.map(([_, info]) => info.num_rows || info.size_kb || 0);
  const yScale = d3.scaleLinear()
    .domain([0, d3.max(values) * 1.1])
    .range([height - margin.bottom, margin.top]);

  svg.append("g")
    .attr("transform", `translate(0,${height - margin.bottom})`)
    .call(d3.axisBottom(xScale))
    .selectAll("text")
    .attr("transform", "rotate(-40)")
    .style("text-anchor", "end");

  svg.append("g")
    .attr("transform", `translate(${margin.left},0)`)
    .call(d3.axisLeft(yScale));

  svg.selectAll("circle")
    .data(files)
    .join("circle")
    .attr("cx", d => xScale(d[0]) + xScale.bandwidth() / 2)
    .attr("cy", d => yScale(d[1].num_rows || d[1].size_kb || 0))
    .attr("r", 8)
    .attr("fill", "#007bff")
    .style("cursor", "pointer")
    .on("mouseover", (event, d) => {
      tooltip
        .style("opacity", 1)
        .html(`
          <strong>${d[0]}</strong><br/>
          Filas: ${d[1].num_rows || "N/A"}<br/>
          Tamaño (KB): ${d[1].size_kb || "N/A"}<br/>
          Codificación: ${d[1].encoding || "N/A"}
        `)
        .style("left", (event.pageX + 15) + "px")
        .style("top", (event.pageY - 28) + "px");
    })
    .on("mousemove", (event) => {
      tooltip
        .style("left", (event.pageX + 15) + "px")
        .style("top", (event.pageY - 28) + "px");
    })
    .on("mouseout", () => {
      tooltip.style("opacity", 0);
    });

  svg.append("text")
    .attr("x", width / 2)
    .attr("y", margin.top / 2)
    .attr("text-anchor", "middle")
    .attr("font-size", "18px")
    .attr("font-weight", "bold")
    .text("Línea de tiempo: filas o tamaño por archivo GTFS");

  svg.append("text")
    .attr("x", width / 2)
    .attr("y", height - 10)
    .attr("text-anchor", "middle")
    .attr("font-size", "12px")
    .text("Archivos (nombres rotados para mejor lectura)");
}



