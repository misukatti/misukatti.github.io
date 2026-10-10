// Fills every docs page's version switcher from versions.json, and says on a page that isn't the
// current release which version it is. Read at view time, so a released version's pages, which are
// never written again, still list the versions that came after them.
(async () => {
	const current = document.body.dataset.docsVersion;
	const select = document.querySelector(".docs-version select");
	const banner = document.querySelector(".docs-banner");
	let versions;
	try {
		versions = await (await fetch("/hammerite/docs/versions.json")).json();
	} catch {
		return;
	}
	const stable = versions.find((v) => v.stable);
	const prefix = `/hammerite/docs/${current}/`;
	const rest = location.pathname.startsWith(prefix) ? location.pathname.slice(prefix.length) : "";

	const samePageIn = async (version) => {
		const page = `/hammerite/docs/${version}/${rest}`;
		try {
			if ((await fetch(page, { method: "HEAD" })).ok) return page + location.hash;
		} catch {}
		return `/hammerite/docs/${version}/`;
	};

	select.replaceChildren(...versions.map((v) => new Option(v.label, v.id, false, v.id === current)));
	select.addEventListener("change", async () => {
		location.href = await samePageIn(select.value);
	});

	if (stable && current !== stable.id) {
		const here = versions.find((v) => v.id === current);
		const what = current === "latest"
			? "These docs are for <strong>latest</strong>: what has changed since the last release, not yet released."
			: `These docs are for Hammerite <strong>${here ? here.label : current}</strong>, an older release.`;
		banner.innerHTML = `${what} <a href="${await samePageIn(stable.id)}">Go to ${stable.id}, the current release →</a>`;
		banner.hidden = false;
	}
})();
