import { Injectable } from '@angular/core';
import { Tenant, Metric } from './types';

export const TENANTS: Tenant[] = [
    {name: 'gigi', metrics: [new Metric({id: 'p1cpu'}), new Metric({id: 'p1mem'})]},
    {name: 'cornel', metrics: [new Metric({id: 'p2cpu'}), new Metric({id: 'p2mem'})]},
];


@Injectable()
export class DataService {
    getTenants(): Tenant[] {
        return TENANTS;
    }
}
