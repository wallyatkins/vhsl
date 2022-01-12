# Virginia High School League (VHSL)

## PostGIS Database Tables

### States

```
create table geo_data.states (id serial primary key, name varchar(256), abbr varchar(2), state_fp varchar(10));
select AddGeometryColumn ('geo_data', 'states', 'geom', 4326, 'MULTIPOLYGON', 2);
```

```
postgis_db=# \d geo_data.states;
                                           Table "geo_data.states"
  Column  |            Type             | Collation | Nullable |                   Default
----------+-----------------------------+-----------+----------+---------------------------------------------
 id       | integer                     |           | not null | nextval('geo_data.states_id_seq'::regclass)
 name     | character varying(256)      |           |          |
 abbr     | character varying(2)        |           |          |
 state_fp | character varying(10)       |           |          |
 geom     | geometry(MultiPolygon,4326) |           |          |
Indexes:
    "states_pkey" PRIMARY KEY, btree (id)
```

### Counties

```
create table geo_data.counties (id serial primary key, name varchar(256), state_fp varchar(10));
select AddGeometryColumn ('geo_data', 'counties', 'geom', 4326, 'MULTIPOLYGON', 2);
```

```
postgis_db=# \d geo_data.counties;
                                           Table "geo_data.counties"
  Column  |            Type             | Collation | Nullable |                    Default
----------+-----------------------------+-----------+----------+-----------------------------------------------
 id       | integer                     |           | not null | nextval('geo_data.counties_id_seq'::regclass)
 name     | character varying(256)      |           |          |
 state_fp | character varying(10)       |           |          |
 geom     | geometry(MultiPolygon,4326) |           |          |
Indexes:
    "counties_pkey" PRIMARY KEY, btree (id)
```

## Create A States Geometry From Counties

```
psql -d postgis_db -c "select ST_AsGeoJson(ST_Union(ST_MakeValid(geom))) as state from geo_data.counties where state_fp = '51'" -o /var/lib/postgresql/virgina.geojson
```
