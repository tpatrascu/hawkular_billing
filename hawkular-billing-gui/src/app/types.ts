export class Tenant {
    name: string;
    metrics: Metric[];
}

export class Metric {
    id: string;

    constructor(private params) {
        this.id = params.id;
    }
}
