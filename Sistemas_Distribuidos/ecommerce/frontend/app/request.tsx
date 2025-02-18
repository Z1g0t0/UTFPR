export default async function Request(url: String) {

	console.log("URL: ", url);

    const res = await fetch(url)
    const data = await res.json() 
	//console.log("DATA: ", JSON.stringify(data, null, 4))

    return data
}

