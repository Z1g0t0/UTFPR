module.exports = {
	reactStrictMode: true,
	env: {
		STRIPE_API_KEY: process.env.STRIPE_API_KEY,
		notificacaoPORT: process.env.notificacaoPORT,
		principalPORT: process.env.principalPORT,
		pagamentoPORT: process.env.pagamentoPORT,
	},
};
